from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EntryCreate(BaseModel):
    title: Optional[str] = None
    content: str
    tags: Optional[List[str]] = None
    is_draft: Optional[bool] = False


class EntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_draft: Optional[bool] = False


class EntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    content: str
    summary: Optional[str] = None
    is_draft: Optional[bool] = False
    mood_rating: Optional[float] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    ai_processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EntryListResponse(BaseModel):
    entries: List[EntryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
