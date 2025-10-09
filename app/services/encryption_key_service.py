from sqlmodel import Session
from uuid import UUID
import secrets

from app.core.crypto import encrypt_data, decrypt_data
from app.core.config import settings
from app.crud.encryption_key import create_encryption_key, get_encryption_key_by_user_id


def generate_user_data_key() -> str:
    # 32 bytes hex key for per-user encryption (placeholder)
    return secrets.token_hex(32)


def create_and_store_wrapped_key(session: Session, *, user_id: UUID) -> str:
    """Generate a per-user data key, wrap it with the master key, and persist.

    Returns the wrapped key string.
    """
    data_key = generate_user_data_key()
    wrapped_key = encrypt_data(data_key, settings.master_encryption_key)
    create_encryption_key(session, user_id=user_id, wrapped_key=wrapped_key)
    return wrapped_key


def get_user_data_key(session: Session, *, user_id: UUID) -> str:
    """Unwrap and return the user's data key using the master key."""
    record = get_encryption_key_by_user_id(session, user_id=user_id)
    if record is None:
        raise ValueError("Encryption key not found for user")
    data_key = decrypt_data(record.wrapped_key, settings.master_encryption_key)
    return data_key


