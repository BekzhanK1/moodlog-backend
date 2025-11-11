from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

from .user import User


class Entry(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: Optional[str] = None
    encrypted_content: str
    encrypted_summary: Optional[str] = None
    is_draft: bool = Field(default=False)
    # AI-analyzed sentiment (-1.0 to +1.0)
    mood_rating: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    tags: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON))  # AI-extracted themes/tags
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # When AI analysis was completed
    ai_processed_at: Optional[datetime] = None

    # Relationships
    user: Optional["User"] = Relationship(back_populates="entries")
