from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Sequence, Union
from . import models

def _ensure_uuid(session_id: Union[str, UUID]) -> UUID:
    if isinstance(session_id, str):
        try:
            return UUID(session_id)
        except ValueError:
            # If it's not a valid UUID, we might want to handle it gracefully or raise error.
            # However, for "sess_" prefixed IDs which are not UUIDs, this will fail.
            # But the user asked to be robust against them.
            # Since the DB expects UUID, we MUST provide a UUID. 
            # If the string is not a UUID, we can't really query a UUID column.
            # We'll let ValueError propagate if it's not a valid UUID string.
            # But for robustness, maybe we just return None or handle it in caller?
            # The prompt says: "Refactor the code to be robust against 'sess_' prefixed session IDs"
            # AND "Update crud.py to accept strings".
            # If the DB column IS UUID, we can't search for "sess_123".
            # So we assume the frontend will be updated to send valid UUIDs, 
            # OR we generate a UUID if it fails? No, that breaks retrieval.
            # Let's stick to standard UUID conversion and let caller handle invalid formats.
            return UUID(session_id)
    return session_id

async def create_session(db: AsyncSession) -> models.Session:
    db_session = models.Session()
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_session(db: AsyncSession, session_id: Union[str, UUID]) -> models.Session | None:
    try:
        uuid_obj = _ensure_uuid(session_id)
    except ValueError:
        return None
        
    result = await db.execute(select(models.Session).where(models.Session.id == uuid_obj))
    return result.scalars().first()

async def create_message(db: AsyncSession, session_id: Union[str, UUID], role: str, content: str) -> models.ChatMessage:
    # Here strictly we need a UUID for the foreign key if enforce FK is on.
    # If session_id is invalid string, this will fail.
    uuid_obj = _ensure_uuid(session_id)
    db_message = models.ChatMessage(session_id=uuid_obj, role=role, content=content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message

async def get_chat_history(db: AsyncSession, session_id: Union[str, UUID]) -> Sequence[models.ChatMessage]:
    try:
        uuid_obj = _ensure_uuid(session_id)
    except ValueError:
        return []

    result = await db.execute(
        select(models.ChatMessage)
        .where(models.ChatMessage.session_id == uuid_obj)
        .order_by(models.ChatMessage.timestamp.asc())
    )
    return result.scalars().all()
