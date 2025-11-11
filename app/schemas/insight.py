from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class InsightResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    period_key: str
    period_label: str
    content: str  # Decrypted content
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InsightListResponse(BaseModel):
    insights: list[InsightResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
