from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class Entry(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: Optional[str] = None
    content: str
    mood_rating: Optional[float] = Field(default=None, ge=-1.0, le=1.0)  # AI-analyzed sentiment (-1.0 to +1.0)
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))  # AI-extracted themes/tags
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    ai_processed_at: Optional[datetime] = None  # When AI analysis was completed
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="entries")
