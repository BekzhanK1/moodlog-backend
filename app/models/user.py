from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4


class User(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None)
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    name: Optional[str] = Field(default=None)
    picture: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Subscription fields
    # "free", "trial", "pro_month", "pro_year"
    plan: str = Field(default="free", index=True)
    plan_started_at: Optional[datetime] = None
    plan_expires_at: Optional[datetime] = None
    trial_used: bool = Field(default=False)
    subscription_status: str = Field(
        default="active", index=True
    )  # "active", "expired", "cancelled"

    # Admin field
    is_admin: bool = Field(default=False, index=True)

    # Relationships
    entries: List["Entry"] = Relationship(back_populates="user")
    encryption_key: Optional["EncryptionKey"] = Relationship(
        back_populates="user")
    characteristic: Optional["UserCharacteristic"] = Relationship(
        back_populates="user")
    subscriptions: List["Subscription"] = Relationship(back_populates="user")
    payments: List["Payment"] = Relationship(back_populates="user")


if TYPE_CHECKING:
    from .entry import Entry
    from .encryption_key import EncryptionKey
    from .user_characteristic import UserCharacteristic
    from .subscription import Subscription
    from .payment import Payment
