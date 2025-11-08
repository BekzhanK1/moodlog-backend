from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4

from typing import TYPE_CHECKING



class User(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: Optional[str] = Field(default=None)
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    name: Optional[str] = Field(default=None)
    picture: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    entries: List["Entry"] = Relationship(back_populates="user")
    encryption_key: Optional["EncryptionKey"] = Relationship(back_populates="user")

if TYPE_CHECKING:
    from .entry import Entry
    from .encryption_key import EncryptionKey

