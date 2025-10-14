from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.db.session import get_session
from app.models import Entry, User
from app.schemas import EntryCreate, EntryUpdate, EntryResponse, EntryListResponse
from app.core.deps import get_current_user
import math
from app.crud import entry as entry_crud
from fastapi import File, UploadFile
from app.services.audio_transcription_service import AudioTranscriptionService
        

router = APIRouter()

_encryption_service = None
_crypto_functions = None
_analysis_service = None
_audio_service = None

def get_audio_service():
    """Lazy load audio transcription service"""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioTranscriptionService()
    return _audio_service

def get_encryption_service():
    """Lazy load encryption service"""
    global _encryption_service
    if _encryption_service is None:
        from app.services.encryption_key_service import get_user_data_key
        _encryption_service = get_user_data_key
    return _encryption_service

def get_crypto_functions():
    """Lazy load crypto functions"""
    global _crypto_functions
    if _crypto_functions is None:
        from app.core.crypto import encrypt_data, decrypt_data
        _crypto_functions = (encrypt_data, decrypt_data)
    return _crypto_functions

def get_analysis_service():
    """Lazy load analysis service"""
    global _analysis_service
    if _analysis_service is None:
        from app.services.entry_analysis_service import MoodAnalysisService
        _analysis_service = MoodAnalysisService()
    return _analysis_service


async def analyze_entry_background(entry_id: UUID, content: str, user_id: UUID):
    """Background task to analyze entry content and update the database"""
    try:
        # Use lazy-loaded analysis service
        mood_analysis_service = get_analysis_service()
        
        # Perform AI analysis
        analysis = mood_analysis_service.analyze_entry(content)
        
        # Create database session directly
        from sqlmodel import Session
        from app.db.session import engine
        
        with Session(engine) as session:
            entry = entry_crud.get_entry_by_id(session, entry_id=entry_id, user_id=user_id)
            if entry:
                entry.mood_rating = analysis["mood_rating"]
                entry.tags = analysis["tags"] if not entry.tags else entry.tags  # Keep user tags if provided
                entry.ai_processed_at = datetime.utcnow()
                session.commit()
                print(f"✅ AI analysis completed for entry {entry_id}")
            else:
                print(f"❌ Entry {entry_id} not found for analysis")
    except Exception as e:
        print(f"❌ Error in background analysis for entry {entry_id}: {e}")


@router.post("/", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    entry_data: EntryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new diary entry"""
    # Use lazy-loaded services
    get_user_data_key = get_encryption_service()
    encrypt_data, decrypt_data = get_crypto_functions()
    
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
    
    background_tasks.add_task(
        analyze_entry_background,
        entry.id,
        entry_data.content,
        current_user.id
    )
    
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
    # Use lazy-loaded services
    get_user_data_key = get_encryption_service()
    encrypt_data, decrypt_data = get_crypto_functions()
    
    offset = (page - 1) * per_page
    
    entries, total = entry_crud.list_entries(
        session,
        user_id=current_user.id,
        offset=offset,
        limit=per_page,
    )
    total_pages = math.ceil(total / per_page) if per_page else 1
    
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
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific diary entry by ID"""
    # Use lazy-loaded services
    get_user_data_key = get_encryption_service()
    encrypt_data, decrypt_data = get_crypto_functions()
    
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
    entry_id: UUID,
    entry_data: EntryUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update a diary entry (full/replace semantics)"""

    # Import encryption functions lazily
    from app.services.encryption_key_service import get_user_data_key
    from app.core.crypto import encrypt_data, decrypt_data
    
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
    
    if entry_data.content is not None:
        background_tasks.add_task(
            analyze_entry_background,
            entry.id,
            entry_data.content,
            current_user.id
        )
    
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
    entry_id: UUID,
    entry_data: EntryUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Partially update a diary entry (PATCH semantics)"""
    # Import encryption functions lazily
    from app.services.encryption_key_service import get_user_data_key
    from app.core.crypto import encrypt_data, decrypt_data
    
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
    
    if entry_data.content is not None:
        background_tasks.add_task(
            analyze_entry_background,
            entry.id,
            entry_data.content,
            current_user.id
        )
    
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
    entry_id: UUID,
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


@router.post("/from-audio", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entry_from_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(..., description="Audio file to transcribe (MP3, WAV, etc.)"),
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new diary entry from audio file.
    
    The audio file will be transcribed to text using Whisper AI,
    then treated as a regular text entry with AI analysis.
    """
    # Get audio service
    audio_service = get_audio_service()
    
    # Validate audio file
    if not audio_service.validate_audio_file(audio_file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio file type. Supported formats: MP3, WAV, M4A, OGG, WEBM"
        )
    
    # Transcribe audio to text
    try:
        content = await audio_service.transcribe_audio(audio_file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}"
        )
    
    # Validate transcription result
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No speech detected in audio file. Please check the audio quality."
        )
    
    # Now treat the transcribed text as a regular entry
    # Use existing entry creation logic
    get_user_data_key = get_encryption_service()
    encrypt_data, decrypt_data = get_crypto_functions()
    
    data_key = get_user_data_key(session, user_id=current_user.id)
    encrypted_content = encrypt_data(content, data_key)
    encrypted_title = encrypt_data(title, data_key) if title is not None else None

    entry = entry_crud.create_entry(
        session,
        user_id=current_user.id,
        title=encrypted_title,
        content=encrypted_content,
        tags=tags,
    )
    
    # Background AI analysis (sentiment + theme extraction)
    background_tasks.add_task(
        analyze_entry_background,
        entry.id,
        content,
        current_user.id
    )
    
    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=title,
        content=content,
        mood_rating=entry.mood_rating,  
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        ai_processed_at=entry.ai_processed_at,
    )


# AI Analysis Functions
def trigger_ai_analysis(entry_id: str):
    """Trigger AI analysis for a diary entry"""
    # Import encryption functions lazily
    from app.services.encryption_key_service import get_user_data_key
    from app.core.crypto import decrypt_data
    from app.services.entry_analysis_service import MoodAnalysisService
    
    mood_analysis_service = MoodAnalysisService()
    
    with get_session() as session:
        entry = entry_crud.get_entry_by_id(session, entry_id=entry_id)
        if not entry:
            return
        
        
        data_key = get_user_data_key(session, user_id=entry.user_id)
        decrypted_content = decrypt_data(entry.encrypted_content, data_key)
        
        analysis = mood_analysis_service.analyze_entry(decrypted_content)
        
        entry.mood_rating = analysis["mood_rating"]
        entry.tags = analysis["tags"]
        entry.ai_processed_at = datetime.utcnow()
        
        session.commit()


def analyze_sentiment(content: str) -> float:
    """Analyze sentiment of diary entry content
    Returns float between -2.0 (very negative) and 2.0 (very positive)
    """
    from app.services.entry_analysis_service import MoodAnalysisService
    mood_analysis_service = MoodAnalysisService()
    analysis = mood_analysis_service.analyze_entry(content)
    return analysis["mood_rating"]


def extract_themes(content: str) -> List[str]:
    """Extract key themes and topics from diary entry"""    
    from app.services.entry_analysis_service import MoodAnalysisService
    mood_analysis_service = MoodAnalysisService()
    analysis = mood_analysis_service.analyze_entry(content)
    return analysis["tags"]

