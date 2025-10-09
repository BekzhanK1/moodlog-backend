from typing import Optional

from sqlmodel import Session, select

from app.models import User


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



