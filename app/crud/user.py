from typing import Optional

from sqlmodel import Session, select

from app.models import User
from app.services.encryption_key_service import create_and_store_wrapped_key


def get_user_by_email(session: Session, *, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def create_user(session: Session, *, email: str, hashed_password: str) -> User:
    user = User(email=email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_id(session: Session, *, user_id: str) -> Optional[User]:
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).first()


def get_user_by_google_id(session: Session, *, google_id: str) -> Optional[User]:
    statement = select(User).where(User.google_id == google_id)
    return session.exec(statement).first()


def create_user_from_google_user(
    session: Session,
    *,
    google_id: str,
    email: str,
    name: str,
    picture: Optional[str] = None
) -> User:
    user = get_user_by_google_id(session, google_id=google_id)

    if user:
        user.email = email
        user.name = name
        user.picture = picture

    else:

        existing_user = get_user_by_email(session, email=email)
        if existing_user:
            existing_user.google_id = google_id
            existing_user.name = name
            existing_user.picture = picture
            user = existing_user

        else:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
                hashed_password=None,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            create_and_store_wrapped_key(session, user_id=user.id)

    session.commit()
    session.refresh(user)
    return user
