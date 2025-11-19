from datetime import datetime
from typing import Optional
from sqlmodel import Relationship, SQLModel, Field
from uuid import UUID
from .user import User


class EncryptionKey(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    wrapped_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="encryption_key")
