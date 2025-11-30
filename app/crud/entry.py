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
    summary: Optional[str],
    tags: Optional[List[str]],
    is_draft: Optional[bool] = False,
    created_at: Optional[datetime] = None,
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
        encrypted_summary=summary,
        tags=tags,
        is_draft=is_draft,
    )
    if created_at is not None:
        entry.created_at = created_at
        entry.updated_at = created_at
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def create_entries_batch(
    session: Session,
    *,
    user_id: UUID,
    entries_data: List[dict],
) -> Tuple[List[Tuple[int, Entry]], List[dict]]:
    """Create multiple entries in a batch.

    Returns:
        Tuple of (created_entries_with_indices, failed_entries_info)
        created_entries_with_indices is a list of (original_index, entry) tuples
        failed_entries_info is a list of dicts with 'index' and 'error' keys
    """
    created_entries = []
    failed_entries = []

    for index, entry_data in enumerate(entries_data):
        try:
            entry = Entry(
                user_id=user_id,
                title=entry_data.get("title"),
                encrypted_content=entry_data.get("content"),
                encrypted_summary=entry_data.get("summary"),
                tags=entry_data.get("tags"),
                is_draft=entry_data.get("is_draft", False),
            )
            if entry_data.get("created_at") is not None:
                entry.created_at = entry_data["created_at"]
                entry.updated_at = entry_data["created_at"]
            session.add(entry)
            created_entries.append((index, entry))
        except Exception as e:
            failed_entries.append({"index": index, "error": str(e)})

    # Commit all successful entries in one transaction
    try:
        session.commit()
        # Refresh all created entries
        for index, entry in created_entries:
            session.refresh(entry)
        return created_entries, failed_entries
    except Exception as e:
        session.rollback()
        # If batch commit fails, mark all as failed
        return [], [
            {"index": i, "error": f"Batch commit failed: {str(e)}"}
            for i in range(len(entries_data))
        ]


def get_entry_by_id(
    session: Session, *, user_id: UUID, entry_id: UUID
) -> Optional[Entry]:
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
    end_date: Optional[date] = None,
) -> List[Entry]:
    now = datetime.now(timezone.utc)
    if start_date is None:
        start_date = now.date() - timedelta(days=30)
    if end_date is None:
        end_date = now.date()

    # Convert dates to datetime at start of day (00:00:00) and end of day (23:59:59.999999)
    start_datetime = datetime.combine(start_date, datetime.min.time()).replace(
        tzinfo=timezone.utc
    )
    # For end_date, we want to include the entire day, so use start of next day and use < instead of <=
    end_datetime = datetime.combine(
        end_date + timedelta(days=1), datetime.min.time()
    ).replace(tzinfo=timezone.utc)

    statement = select(Entry).where(
        Entry.user_id == user_id,
        Entry.created_at >= start_datetime,
        Entry.created_at < end_datetime,
    )
    entries = session.exec(statement).all()
    return entries


def get_recent_entries(
    session: Session,
    *,
    user_id: UUID,
    limit: int = 5,
    exclude_drafts: bool = True,
) -> List[Entry]:
    """Get recent entries for a user, ordered by created_at descending.

    Args:
        session: Database session
        user_id: User ID
        limit: Maximum number of entries to return
        exclude_drafts: If True, exclude draft entries

    Returns:
        List of Entry objects, most recent first
    """
    statement = select(Entry).where(Entry.user_id == user_id)

    if exclude_drafts:
        statement = statement.where(Entry.is_draft.is_(False))

    statement = statement.order_by(Entry.created_at.desc()).limit(limit)
    entries = session.exec(statement).all()
    return entries


def search_entries(
    session: Session,
    *,
    user_id: UUID,
    query: str,
    offset: int = 0,
    limit: int = 10,
) -> Tuple[List[Entry], int]:
    """Search entries by title, content, or tags.

    Note: Since title and content are encrypted, we need to decrypt them first.
    This function returns all entries for the user, and filtering by query
    should be done after decryption in the API layer.

    For tags, we can search directly in the JSON field.
    """
    # Check if query starts with # for tag search
    is_tag_search = query.startswith("#")
    tag_to_search = query[1:].strip() if is_tag_search else None

    # Base query for user's entries
    base_statement = select(Entry).where(Entry.user_id == user_id)

    if is_tag_search and tag_to_search:
        # Search by tag (tags are stored as JSON array)
        # SQLModel/SQLAlchemy JSON contains check
        # We'll need to check if the tag exists in the tags array
        # Since tags is a JSON column, we need to use a JSON function
        # For PostgreSQL: tags @> '["tag"]'::jsonb
        # For SQLite: we'll need to check differently
        # Let's use a simpler approach: get all entries and filter in Python
        # Or use JSON_EXTRACT for SQLite
        statement = base_statement.order_by(Entry.created_at.desc())
    else:
        # For title/content search, we'll get all entries and filter after decryption
        statement = base_statement.order_by(Entry.created_at.desc())

    # Get all entries (we'll filter after decryption for title/content)
    all_entries = session.exec(statement).all()

    # Filter by tag if it's a tag search
    if is_tag_search and tag_to_search:
        filtered_entries = [
            e
            for e in all_entries
            if e.tags and tag_to_search.lower() in [tag.lower() for tag in e.tags]
        ]
        total = len(filtered_entries)
        paginated_entries = filtered_entries[offset: offset + limit]
        return paginated_entries, total

    # For non-tag searches, return all entries (will be filtered after decryption)
    total = len(all_entries)
    paginated_entries = all_entries[offset: offset + limit]
    return paginated_entries, total
