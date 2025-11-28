from sqlmodel import Session, select
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.user_characteristic import UserCharacteristic


def get_user_characteristic(
    session: Session, *, user_id: UUID
) -> Optional[UserCharacteristic]:
    """Get user characteristics by user ID"""
    statement = select(UserCharacteristic).where(UserCharacteristic.user_id == user_id)
    return session.exec(statement).first()


def create_or_update_characteristic(
    session: Session,
    *,
    user_id: UUID,
    general_description: Optional[str] = None,
    main_themes: Optional[list] = None,
    emotional_profile: Optional[Dict[str, Any]] = None,
    writing_style: Optional[Dict[str, Any]] = None,
) -> UserCharacteristic:
    """Create or update user characteristics"""
    existing = get_user_characteristic(session, user_id=user_id)

    if existing:
        # Update existing
        if general_description is not None:
            existing.general_description = general_description
        if main_themes is not None:
            existing.main_themes = main_themes
        if emotional_profile is not None:
            existing.emotional_profile = emotional_profile
        if writing_style is not None:
            existing.writing_style = writing_style
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Create new
        characteristic = UserCharacteristic(
            user_id=user_id,
            general_description=general_description,
            main_themes=main_themes,
            emotional_profile=emotional_profile,
            writing_style=writing_style,
        )
        session.add(characteristic)
        session.commit()
        session.refresh(characteristic)
        return characteristic
