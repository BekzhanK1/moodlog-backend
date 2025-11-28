from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from .user import User


class UserCharacteristic(SQLModel, table=True):
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", unique=True, index=True)

    # General description
    general_description: Optional[str] = None

    # Main themes (stored as JSON array)
    main_themes: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    # Emotional profile (stored as JSON)
    emotional_profile: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

    # Writing style (stored as JSON)
    writing_style: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    user: Optional["User"] = Relationship(back_populates="characteristic")
