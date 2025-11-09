from datetime import datetime, timedelta, date, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlmodel import Session, select

from app.models import Entry


def create_entry(
    session: Session,
    *,
    user_id: UUID,
    title: Optional[str],
    content: str,
    tags: Optional[List[str]],
    is_draft: Optional[bool] = False,
) -> Entry:
    """Create a new entry for a user.

    Note: The Entry model uses `encrypted_content`. At this layer we simply
    accept `content` assuming upstream encryption has occurred or content is
    plaintext until encryption is implemented.
    """
    entry = Entry(
        user_id=user_id,
        title=title,
        encrypted_content=content,
        tags=tags,
        is_draft=is_draft,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def get_entry_by_id(session: Session, *, user_id: UUID, entry_id: UUID) -> Optional[Entry]:
    statement = select(Entry).where(
        Entry.id == entry_id, Entry.user_id == user_id)
    return session.exec(statement).first()


def list_entries(
    session: Session,
    *,
    user_id: UUID,
    offset: int,
    limit: int,
) -> Tuple[List[Entry], int]:
    count_statement = select(Entry).where(Entry.user_id == user_id)
    total = len(session.exec(count_statement).all())

    statement = (
        select(Entry)
        .where(Entry.user_id == user_id)
        .order_by(Entry.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    entries = session.exec(statement).all()
    return entries, total


def update_entry(
    session: Session,
    *,
    user_id: UUID,
    entry_id: UUID,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
    is_draft: Optional[bool] = None,
) -> Optional[Entry]:
    entry = get_entry_by_id(session, user_id=user_id, entry_id=entry_id)
    if entry is None:
        return None

    if title is not None:
        entry.title = title
    if content is not None:
        entry.encrypted_content = content
    if tags is not None:
        entry.tags = tags
    if is_draft is not None:
        entry.is_draft = is_draft
    entry.updated_at = datetime.utcnow()

    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def delete_entry(session: Session, *, user_id: UUID, entry_id: UUID) -> bool:
    entry = get_entry_by_id(session, user_id=user_id, entry_id=entry_id)
    if entry is None:
        return False
    session.delete(entry)
    session.commit()
    return True


def get_entries_by_date_range(
    session: Session,
    *,
    user_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Entry]:
    now = datetime.now(timezone.utc)
    if start_date is None:
        start_date = now.date() - timedelta(days=30)
    if end_date is None:
        end_date = now.date()

    # Convert dates to datetime at start of day (00:00:00) and end of day (23:59:59.999999)
    start_datetime = datetime.combine(
        start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    # For end_date, we want to include the entire day, so use start of next day and use < instead of <=
    end_datetime = datetime.combine(
        end_date + timedelta(days=1), datetime.min.time()).replace(tzinfo=timezone.utc)

    statement = (
        select(Entry)
        .where(
            Entry.user_id == user_id,
            Entry.created_at >= start_datetime,
            Entry.created_at < end_datetime
        )
    )
    entries = session.exec(statement).all()
    return entries
