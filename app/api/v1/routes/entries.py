from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from app.db.session import get_session
from app.models import Entry, User
from app.schemas import EntryCreate, EntryUpdate, EntryResponse, EntryListResponse
from app.core.deps import get_current_user
import math
from app.crud import entry as entry_crud
from app.services.encryption_key_service import get_user_data_key
from app.core.crypto import encrypt_data, decrypt_data

router = APIRouter()


@router.post("/", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    entry_data: EntryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new diary entry"""
    # Encrypt content with user's data key
    data_key = get_user_data_key(session, user_id=current_user.id)
    encrypted_content = encrypt_data(entry_data.content, data_key)
    encrypted_title = encrypt_data(entry_data.title, data_key) if entry_data.title is not None else None

    entry = entry_crud.create_entry(
        session,
        user_id=current_user.id,
        title=encrypted_title,
        content=encrypted_content,
        tags=entry_data.tags,
    )
    
    # TODO: AI - Trigger AI analysis after entry creation
    # await trigger_ai_analysis(entry.id)
    
    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=entry_data.title,
        content=entry_data.content,
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        ai_processed_at=entry.ai_processed_at,
    )


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
    
    entries, total = entry_crud.list_entries(
        session,
        user_id=current_user.id,
        offset=offset,
        limit=per_page,
    )
    total_pages = math.ceil(total / per_page) if per_page else 1
    
    # Decrypt content for response
    data_key = get_user_data_key(session, user_id=current_user.id)
    response_entries = [
        EntryResponse(
            id=e.id,
            user_id=e.user_id,
            title=decrypt_data(e.title, data_key) if e.title is not None else None,
            content=decrypt_data(e.encrypted_content, data_key),
            mood_rating=e.mood_rating,
            tags=e.tags,
            created_at=e.created_at,
            updated_at=e.updated_at,
            ai_processed_at=e.ai_processed_at,
        )
        for e in entries
    ]

    return EntryListResponse(
        entries=response_entries,
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
    entry = entry_crud.get_entry_by_id(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
    )
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # Decrypt content for response
    data_key = get_user_data_key(session, user_id=current_user.id)
    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=decrypt_data(entry.title, data_key) if entry.title is not None else None,
        content=decrypt_data(entry.encrypted_content, data_key),
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        ai_processed_at=entry.ai_processed_at,
    )


@router.put("/{entry_id}", response_model=EntryResponse)
def update_entry(
    entry_id: str,
    entry_data: EntryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a diary entry (full/replace semantics)"""
    # Encrypt new content if provided
    encrypted_content = None
    if entry_data.content is not None:
        data_key = get_user_data_key(session, user_id=current_user.id)
        encrypted_content = encrypt_data(entry_data.content, data_key)
    
    encrypted_title = None
    if entry_data.title is not None:
        data_key = get_user_data_key(session, user_id=current_user.id)
        encrypted_title = encrypt_data(entry_data.title, data_key)

    entry = entry_crud.update_entry(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
        title=encrypted_title,
        content=encrypted_content,
        tags=entry_data.tags,
    )

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # TODO: AI - Trigger AI re-analysis after entry update
    # await trigger_ai_analysis(entry.id)
    
    # Decrypt content for response
    data_key = get_user_data_key(session, user_id=current_user.id)
    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=decrypt_data(entry.title, data_key) if entry.title is not None else None,
        content=decrypt_data(entry.encrypted_content, data_key),
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        ai_processed_at=entry.ai_processed_at,
    )


@router.patch("/{entry_id}", response_model=EntryResponse)
def patch_entry(
    entry_id: str,
    entry_data: EntryUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Partially update a diary entry (PATCH semantics)"""
    # Encrypt new content if provided
    encrypted_content = None
    if entry_data.content is not None:
        data_key = get_user_data_key(session, user_id=current_user.id)
        encrypted_content = encrypt_data(entry_data.content, data_key)

    encrypted_title = None
    if entry_data.title is not None:
        data_key = get_user_data_key(session, user_id=current_user.id)
        encrypted_title = encrypt_data(entry_data.title, data_key)

    entry = entry_crud.update_entry(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
        title=encrypted_title,
        content=encrypted_content,
        tags=entry_data.tags,
    )

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    # TODO: AI - Trigger AI re-analysis after entry partial update
    # await trigger_ai_analysis(entry.id)
    
    # Decrypt content for response
    data_key = get_user_data_key(session, user_id=current_user.id)
    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=decrypt_data(entry.title, data_key) if entry.title is not None else None,
        content=decrypt_data(entry.encrypted_content, data_key),
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        ai_processed_at=entry.ai_processed_at,
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a diary entry"""
    entry = entry_crud.get_entry_by_id(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    entry_crud.delete_entry(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
    )
    
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

