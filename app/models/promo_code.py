from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class PromoCode(SQLModel, table=True):
    """Promo code model for subscription plan redemption."""

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(unique=True, index=True)  # The promo code string
    plan: str = Field(index=True)  # "pro_month" or "pro_year"
    created_by: UUID = Field(foreign_key="user.id", index=True)  # Admin who created it

    # Usage tracking
    max_uses: int = Field(default=1)  # How many times this promo code can be used
    uses_count: int = Field(default=0)  # How many times it has been used

    # Backwards-compatible fields: last user + exhaustion flag
    used_by: Optional[UUID] = Field(
        foreign_key="user.id", nullable=True, index=True
    )  # Last user who redeemed it
    used_at: Optional[datetime] = None  # When it was last redeemed
    is_used: bool = Field(default=False, index=True)  # True when uses_count >= max_uses

    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Optional expiration date

    # Relationships omitted - use CRUD operations to query related users
