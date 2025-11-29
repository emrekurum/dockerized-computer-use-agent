from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Sequence
from . import models

async def create_session(db: AsyncSession) -> models.Session:
    db_session = models.Session()
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_session(db: AsyncSession, session_id: UUID) -> models.Session | None:
    result = await db.execute(select(models.Session).where(models.Session.id == session_id))
    return result.scalars().first()

async def create_message(db: AsyncSession, session_id: UUID, role: str, content: str) -> models.ChatMessage:
    db_message = models.ChatMessage(session_id=session_id, role=role, content=content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_chat_history(db: AsyncSession, session_id: UUID) -> Sequence[models.ChatMessage]:
    result = await db.execute(
        select(models.ChatMessage)
        .where(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.timestamp.asc())
    )
    return result.scalars().all()
