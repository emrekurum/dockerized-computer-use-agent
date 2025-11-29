from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageResponse(MessageCreate):
    id: int
    session_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    pass

class SessionResponse(BaseModel):
    id: UUID
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

