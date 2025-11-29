from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from contextlib import asynccontextmanager

from . import crud, schemas
from .database import engine, Base, SessionLocal
from .agent import run_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Clean up resources if needed
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@app.post("/api/session", response_model=schemas.SessionResponse)
async def create_new_session(db: AsyncSession = Depends(get_db)):
    return await crud.create_session(db)

@app.get("/api/session/{session_id}/history", response_model=List[schemas.MessageResponse])
async def get_session_history(session_id: UUID, db: AsyncSession = Depends(get_db)):
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await crud.get_chat_history(db, session_id)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: UUID):
    await websocket.accept()
    
    # Create a DB session for the websocket connection
    async with SessionLocal() as db:
        try:
            # Verify session exists
            session = await crud.get_session(db, session_id)
            if not session:
                await websocket.close(code=4004, reason="Session not found")
                return

            while True:
                data = await websocket.receive_text()
                
                # 1. Save User Message
                await crud.create_message(db, session_id, "user", data)
                
                # 2. Get History
                history = await crud.get_chat_history(db, session_id)
                
                # 3. Run Agent
                async for event in run_agent(str(session_id), data, history):
                    if event["type"] == "db_save":
                        # Internal event to save agent/tool responses to DB
                        role = event["role"]
                        content = event["content"]
                        await crud.create_message(db, session_id, role, content)
                    else:
                        # Send UI event to client
                        await websocket.send_json(event)
                        
        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_json({"type": "error", "content": str(e)})
