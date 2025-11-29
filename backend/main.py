import traceback
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Sequence, Union
from uuid import UUID
from contextlib import asynccontextmanager

from . import crud, schemas, models
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
async def get_session_history(session_id: str, db: AsyncSession = Depends(get_db)) -> Sequence[schemas.MessageResponse]:
    # session_id is accepted as str to avoid validation error on non-UUID strings
    session = await crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await crud.get_chat_history(db, session_id) # type: ignore

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    print(f"WebSocket connected: {session_id}")
    
    try:
        # Create a DB session for the websocket connection
        async with SessionLocal() as db:
            # 1. Ensure session exists in DB
            # crud functions now handle string session_id and try conversion
            session = await crud.get_session(db, session_id)
            
            if not session:
                # Automatically create the session if it doesn't exist
                try:
                    # Ensure it's a valid UUID before creating
                    session_uuid = UUID(session_id)
                    new_session = models.Session(id=session_uuid)
                    db.add(new_session)
                    await db.commit()
                    await db.refresh(new_session)
                    print(f"Created new session: {session_id}")
                    session = new_session
                except ValueError:
                    print(f"Invalid UUID format for session_id: {session_id}")
                    await websocket.close(code=4000, reason="Invalid UUID")
                    return
                except Exception as e:
                    print(f"Error creating session: {e}")
                    await websocket.close(code=1011, reason="Failed to create session")
                    return

            # 2. Get history (print error if fails)
            try:
                history_seq = await crud.get_chat_history(db, session_id)
                history = list(history_seq)
            except Exception as e:
                print(f"Error fetching history: {e}")
                history = []

            while True:
                data = await websocket.receive_text()
                print(f"Received message: {data}")
                
                # Save User Message to DB
                user_msg = await crud.create_message(db, session_id, "user", data)
                # Append to local history so we don't need to re-fetch
                history.append(user_msg)
                
                # Run Agent
                async for event in run_agent(session_id, data, history):
                    if event["type"] == "db_save":
                        # Internal event: Save Assistant/Tool response to DB
                        role = event["role"]
                        content = event["content"]
                        saved_msg = await crud.create_message(db, session_id, role, content)
                        # Append to local history
                        history.append(saved_msg)
                    
                    elif event["type"] == "error":
                        # Send error to client and print
                        print(f"Agent Error: {event['content']}")
                        await websocket.send_json(event)
                    
                    else:
                        # Forward other events (text, tool_use, tool_result, image) to UI
                        await websocket.send_json(event)
                        
    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        print("CRITICAL WEBSOCKET ERROR:")
        traceback.print_exc() # This will show us the bug!
        try:
            await websocket.close(code=1011)
        except:
            # If connection is already closed, ignore
            pass
