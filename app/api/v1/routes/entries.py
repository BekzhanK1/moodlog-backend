from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from app.db.session import get_session
from app.models import Entry, User
from app.schemas import EntryCreate, EntryUpdate, EntryResponse, EntryListResponse
from app.core.deps import get_current_user
import math

router = APIRouter()


@router.post("/", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    entry_data: EntryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new diary entry"""
    entry = Entry(
        user_id=current_user.id,
        title=entry_data.title,
        content=entry_data.content,
        tags=entry_data.tags
        # mood_rating will be set by AI analysis
    )
    
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    # TODO: AI - Trigger AI analysis after entry creation
    # await trigger_ai_analysis(entry.id)
    
    return entry


@router.get("/", response_model=EntryListResponse)
def get_entries(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Entries per page"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get paginated list of user's diary entries"""
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get total count
    count_statement = select(Entry).where(Entry.user_id == current_user.id)
    total = len(session.exec(count_statement).all())
    
    # Get paginated entries
    statement = (
        select(Entry)
        .where(Entry.user_id == current_user.id)
        .order_by(Entry.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    
    entries = session.exec(statement).all()
    total_pages = math.ceil(total / per_page) if per_page else 1
    
    return EntryListResponse(
        entries=entries,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{entry_id}", response_model=EntryResponse)
def get_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific diary entry by ID"""
    statement = select(Entry).where(
        Entry.id == entry_id,
        Entry.user_id == current_user.id
    )
    entry = session.exec(statement).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    return entry


@router.put("/{entry_id}", response_model=EntryResponse)
def update_entry(
    entry_id: str,
    entry_data: EntryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a diary entry (full/replace semantics)"""
    statement = select(Entry).where(
        Entry.id == entry_id,
        Entry.user_id == current_user.id
    )
    entry = session.exec(statement).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # Replace semantics: set provided fields, keep others
    update_data = entry_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    entry.updated_at = datetime.utcnow()
    
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    # TODO: AI - Trigger AI re-analysis after entry update
    # await trigger_ai_analysis(entry.id)
    
    return entry


@router.patch("/{entry_id}", response_model=EntryResponse)
def patch_entry(
    entry_id: str,
    entry_data: EntryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Partially update a diary entry (PATCH semantics)"""
    statement = select(Entry).where(
        Entry.id == entry_id,
        Entry.user_id == current_user.id
    )
    entry = session.exec(statement).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    update_data = entry_data.dict(exclude_unset=True)
    if not update_data:
        return entry
    for field, value in update_data.items():
        setattr(entry, field, value)
    entry.updated_at = datetime.utcnow()
    
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    # TODO: AI - Trigger AI re-analysis after entry partial update
    # await trigger_ai_analysis(entry.id)
    
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a diary entry"""
    statement = select(Entry).where(
        Entry.id == entry_id,
        Entry.user_id == current_user.id
    )
    entry = session.exec(statement).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    session.delete(entry)
    session.commit()
    
    return None


# TODO: AI - Placeholder functions for future AI features
async def trigger_ai_analysis(entry_id: str):
    """Trigger AI analysis for a diary entry"""
    # This will be implemented in Phase 2
    # Will analyze sentiment (mood_rating) and extract themes (tags)
    pass


async def analyze_sentiment(content: str) -> float:
    """Analyze sentiment of diary entry content"""
    # TODO: AI - Implement sentiment analysis using NLP models
    # Returns float between -1.0 (very negative) and 1.0 (very positive)
    pass


async def extract_themes(content: str) -> List[str]:
    """Extract key themes and topics from diary entry"""
    # TODO: AI - Implement theme extraction using NLP
    # Returns list of key themes/topics from the content
    pass

