from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .user import User
    from .subscription import Subscription


class Payment(SQLModel, table=True):
    """Payment model to store all payment transactions and Webkassa.kz integration data."""

    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    subscription_id: Optional[UUID] = Field(
        foreign_key="subscription.id", nullable=True, index=True
    )

    # Payment details
    amount: float  # Amount in KZT
    currency: str = Field(default="KZT")
    plan: str = Field(index=True)  # "pro_month", "pro_year"

    # Webkassa.kz integration
    webkassa_order_id: Optional[str] = Field(
        default=None, unique=True, index=True
    )  # Order ID from webkassa
    webkassa_receipt_id: Optional[str] = Field(
        default=None, index=True
    )  # Fiscal receipt ID
    webkassa_status: Optional[str] = Field(
        default=None, index=True
    )  # "pending", "success", "failed"

    # Payment status
    # "pending", "completed", "failed", "refunded"
    status: str = Field(index=True)
    payment_method: Optional[str] = None  # "card", "bank_transfer", etc.

    # Payment metadata (stored as JSON)
    payment_metadata: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Relationships
    user: Optional["User"] = Relationship(back_populates="payments")
    subscription: Optional["Subscription"] = Relationship(
        back_populates="payments")
