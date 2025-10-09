from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EntryCreate(BaseModel):
    title: Optional[str] = None
    content: str
    tags: Optional[List[str]] = None
    # Note: mood_rating will be analyzed by AI, not input by user


class EntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    # Note: mood_rating is AI-analyzed, not user-editable


class EntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    content: str
    mood_rating: Optional[float] = None  # AI-analyzed sentiment (-1.0 to +1.0)
    tags: Optional[List[str]] = None  # AI-extracted themes/tags
    created_at: datetime
    updated_at: datetime
    ai_processed_at: Optional[datetime] = None  # When AI analysis was completed
    
    class Config:
        from_attributes = True


class EntryListResponse(BaseModel):
    entries: List[EntryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
