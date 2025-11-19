from typing import Optional
from uuid import UUID
from sqlmodel import Session, select

from app.models import EncryptionKey


def get_encryption_key_by_user_id(
    session: Session, *, user_id: UUID
) -> Optional[EncryptionKey]:
    statement = select(EncryptionKey).where(EncryptionKey.user_id == user_id)
    return session.exec(statement).first()


def create_encryption_key(
    session: Session, *, user_id: UUID, wrapped_key: str
) -> EncryptionKey:
    encryption_key = EncryptionKey(user_id=user_id, wrapped_key=wrapped_key)
    session.add(encryption_key)
    session.commit()
    session.refresh(encryption_key)
    return encryption_key
