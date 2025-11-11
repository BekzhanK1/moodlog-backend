from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID, uuid4


class Insight(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")

    # 'monthly' | 'weekly' | 'specific' | 'custom' (kept as string for flexibility)
    type: str = Field(index=True)

    # Canonical period identifier, e.g. '2025-11', '2025-W46', or custom for 'specific'
    period_key: str = Field(index=True)
    # Human-readable label, e.g. 'November 2025', 'Week 46, 2025'
    period_label: str

    # Time window this insight summarizes (optional, useful for querying)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Encrypted content (same pattern as entries)
    encrypted_content: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Uniqueness at business-level: one insight per user/type/period
    # (enforced via code and optionally via DB migration unique index)
