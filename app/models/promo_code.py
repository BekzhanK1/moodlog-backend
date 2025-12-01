from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class PromoCode(SQLModel, table=True):
    """Promo code model for one-time plan redemption."""

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(unique=True, index=True)  # The promo code string
    plan: str = Field(index=True)  # "pro_month" or "pro_year"
    created_by: UUID = Field(foreign_key="user.id", index=True)  # Admin who created it
    used_by: Optional[UUID] = Field(
        foreign_key="user.id", nullable=True, index=True
    )  # User who redeemed it
    used_at: Optional[datetime] = None  # When it was redeemed
    is_used: bool = Field(default=False, index=True)  # Whether it's been used
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # Optional expiration date

    # Relationships omitted - use CRUD operations to query related users
