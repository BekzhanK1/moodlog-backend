from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .user import User
    from .payment import Payment


class Subscription(SQLModel, table=True):
    """Subscription model to track user subscription history and changes."""

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    plan: str = Field(index=True)  # "free", "trial", "pro_month", "pro_year"
    # "active", "expired", "cancelled", "pending"
    status: str = Field(index=True)
    started_at: datetime
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="subscriptions")
    payments: List["Payment"] = Relationship(back_populates="subscription")
