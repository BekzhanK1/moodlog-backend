from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.core.crypto import encrypt_data
from app.db.session import get_session
from app.models import User
from app.schemas import EntryCreate, EntryUpdate, EntryResponse, EntryListResponse, BatchEntryCreate, BatchEntryResponse
from app.core.deps import get_current_user
import math
from app.crud import entry as entry_crud
from fastapi import File, UploadFile
from app.services.audio_transcription_service import AudioTranscriptionService
import asyncio
from concurrent.futures import ThreadPoolExecutor


router = APIRouter()

# Thread pool executor for running blocking AI analysis tasks in parallel
_analysis_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="ai_analysis")

_encryption_service = None
_crypto_functions = None
_analysis_service = None
_audio_service = None
_summarizer_service = None


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


def get_summarizer_service():
    """Lazy load summarizer service"""
    global _summarizer_service
    if _summarizer_service is None:
        from app.services.ai_summarizer import AISummarizerService

        _summarizer_service = AISummarizerService()
    return _summarizer_service


def _analyze_entry_sync(
    entry_id: UUID, content: str, user_id: UUID, data_key: Optional[str] = None
):
    """Synchronous function to analyze entry content and update the database.
    This runs in a thread pool executor to avoid blocking."""
    try:
        # Use lazy-loaded analysis service
        mood_analysis_service = get_analysis_service()

        # Perform AI analysis
        analysis = mood_analysis_service.analyze_entry(content)

        # Conditionally summarize entries > 100 words
        word_count = len(content.split())
        encrypted_summary = None
        if word_count > 100:
            summarizer_service = get_summarizer_service()
            summary = summarizer_service.summarize_entry(content)
            print(f"Summary ⚡: {summary}")
            if summary and data_key:
                encrypted_summary = encrypt_data(summary, data_key)
        else:
            print(f"⏭️ Skipping summarization for short entry ({word_count} words)")

        # Create database session directly
        from sqlmodel import Session
        from app.db.session import engine

        with Session(engine) as session:
            entry = entry_crud.get_entry_by_id(
                session, entry_id=entry_id, user_id=user_id
            )
            if entry:
                # Skip analysis if entry is a draft
                if entry.is_draft:
                    print(f"⏭️ Skipping AI analysis for draft entry {entry_id}")
                    return

                entry.mood_rating = analysis["mood_rating"]
                # Always update tags from AI analysis (they reflect the current content)
                entry.tags = analysis["tags"]
                entry.encrypted_summary = encrypted_summary
                entry.ai_processed_at = datetime.utcnow()
                session.commit()
                print(f"✅ AI analysis completed for entry {entry_id}")
            else:
                print(f"❌ Entry {entry_id} not found for analysis")
    except Exception as e:
        print(f"❌ Error in background analysis for entry {entry_id}: {e}")


async def analyze_entry_background(
    entry_id: UUID, content: str, user_id: UUID, data_key: Optional[str] = None
):
    """Background task to analyze entry content and update the database.
    Runs the blocking analysis in a thread pool executor for parallel processing."""
    # Use get_running_loop() for Python 3.7+ (more reliable in async contexts)
    # Falls back to get_event_loop() if not in a running loop (e.g., called from BackgroundTasks)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    
    await loop.run_in_executor(
        _analysis_executor,
        _analyze_entry_sync,
        entry_id,
        content,
        user_id,
        data_key,
    )


@router.post("/", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    entry_data: EntryCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new diary entry"""
    # Use lazy-loaded services
    get_user_data_key = get_encryption_service()
    encrypt_data, decrypt_data = get_crypto_functions()

    data_key = get_user_data_key(session, user_id=current_user.id)
    encrypted_content = encrypt_data(entry_data.content, data_key)
    encrypted_title = (
        encrypt_data(entry_data.title, data_key)
        if entry_data.title is not None
        else None
    )

    entry = entry_crud.create_entry(
        session,
        user_id=current_user.id,
        title=encrypted_title,
        content=encrypted_content,
        summary=None,  # Will be set by background task
        tags=entry_data.tags,
        is_draft=entry_data.is_draft,
        created_at=entry_data.created_at,
    )

    # Only analyze if entry is not a draft
    if not entry_data.is_draft:
        background_tasks.add_task(
            analyze_entry_background,
            entry.id,
            entry_data.content,
            current_user.id,
            data_key,
        )

    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=entry_data.title,
        content=entry_data.content,
        summary=(
            decrypt_data(entry.encrypted_summary, data_key)
            if entry.encrypted_summary is not None
            else None
        ),
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        is_draft=entry.is_draft,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        ai_processed_at=entry.ai_processed_at,
    )


@router.post("/batch", response_model=BatchEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_entries_batch(
    batch_data: BatchEntryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create multiple diary entries in a single batch request.
    AI analysis runs asynchronously in parallel after entries are created."""
    # Use lazy-loaded services
    get_user_data_key = get_encryption_service()
    encrypt_data, decrypt_data = get_crypto_functions()

    data_key = get_user_data_key(session, user_id=current_user.id)
    
    # Prepare entries data with encryption
    entries_data = []
    original_contents = []  # Store original content for background tasks
    
    for entry_data in batch_data.entries:
        encrypted_content = encrypt_data(entry_data.content, data_key)
        encrypted_title = (
            encrypt_data(entry_data.title, data_key)
            if entry_data.title is not None
            else None
        )
        
        entries_data.append({
            'title': encrypted_title,
            'content': encrypted_content,
            'summary': None,  # Will be set by background task
            'tags': entry_data.tags,
            'is_draft': entry_data.is_draft,
            'created_at': entry_data.created_at,
        })
        original_contents.append(entry_data.content)
    
    # Create entries in batch
    created_entries_with_indices, failed_entries = entry_crud.create_entries_batch(
        session,
        user_id=current_user.id,
        entries_data=entries_data,
    )
    
    # Schedule background tasks for non-draft entries asynchronously
    # Use asyncio.create_task to run them in parallel without blocking the response
    for original_index, entry in created_entries_with_indices:
        entry_data = batch_data.entries[original_index]
        if not entry_data.is_draft:
            # Create task to run analysis in parallel (fire and forget)
            # Tasks will run concurrently in the thread pool executor
            asyncio.create_task(
                analyze_entry_background(
                    entry.id,
                    original_contents[original_index],
                    current_user.id,
                    data_key,
                )
            )
    
    # Build response with decrypted data
    response_entries = [
        EntryResponse(
            id=entry.id,
            user_id=entry.user_id,
            title=decrypt_data(entry.title, data_key) if entry.title is not None else None,
            content=original_contents[original_index],
            summary=None,  # Will be set by background task
            mood_rating=entry.mood_rating,
            tags=entry.tags,
            is_draft=entry.is_draft,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            ai_processed_at=entry.ai_processed_at,
        )
        for original_index, entry in created_entries_with_indices
    ]
    
    # Build failed entries info
    failed_info = []
    for failed in failed_entries:
        idx = failed['index']
        if idx < len(batch_data.entries):
            failed_info.append({
                'entry': {
                    'content': batch_data.entries[idx].content[:100] + '...' if len(batch_data.entries[idx].content) > 100 else batch_data.entries[idx].content,
                    'created_at': batch_data.entries[idx].created_at.isoformat() if batch_data.entries[idx].created_at else None,
                },
                'error': failed['error']
            })
    
    return BatchEntryResponse(
        created=response_entries,
        failed=failed_info,
        total_requested=len(batch_data.entries),
        total_created=len(created_entries_with_indices),
        total_failed=len(failed_entries),
    )


@router.get("/", response_model=EntryListResponse)
def get_entries(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Entries per page"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
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
            summary=(
                decrypt_data(e.encrypted_summary, data_key)
                if e.encrypted_summary is not None
                else None
            ),
            mood_rating=e.mood_rating,
            tags=e.tags,
            is_draft=e.is_draft,
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
        total_pages=total_pages,
    )


@router.get("/search", response_model=EntryListResponse)
def search_entries(
    q: str = Query(..., description="Search query (use #tag for tag search)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Entries per page"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Search entries by title, content, or tags.

    Use #tag format to search by tags (e.g., #work, #personal).
    Regular text searches in title and content.
    """
    # Use lazy-loaded services
    get_user_data_key = get_encryption_service()
    encrypt_data, decrypt_data = get_crypto_functions()

    data_key = get_user_data_key(session, user_id=current_user.id)

    # Decrypt and filter entries
    is_tag_search = q.startswith("#")
    search_query = q[1:].strip().lower() if is_tag_search else q.lower()

    # For non-tag searches, we need to get all entries first, filter them, then paginate
    # For tag searches, CRUD already filters, so we can paginate directly
    if is_tag_search:
        # Tag search: CRUD already filters, so we can paginate directly
        offset = (page - 1) * per_page
        entries, total = entry_crud.search_entries(
            session,
            user_id=current_user.id,
            query=q,
            offset=offset,
            limit=per_page,
        )

        # Decrypt entries
        response_entries = []
        for e in entries:
            decrypted_title = (
                decrypt_data(e.title, data_key) if e.title is not None else None
            )
            decrypted_content = decrypt_data(e.encrypted_content, data_key)

            response_entries.append(
                EntryResponse(
                    id=e.id,
                    user_id=e.user_id,
                    title=decrypted_title,
                    content=decrypted_content,
                    summary=(
                        decrypt_data(e.encrypted_summary, data_key)
                        if e.encrypted_summary is not None
                        else None
                    ),
                    mood_rating=e.mood_rating,
                    tags=e.tags,
                    is_draft=e.is_draft,
                    created_at=e.created_at,
                    updated_at=e.updated_at,
                    ai_processed_at=e.ai_processed_at,
                )
            )
    else:
        # Non-tag search: get all entries, filter after decryption, then paginate
        all_entries, _ = entry_crud.search_entries(
            session,
            user_id=current_user.id,
            query=q,
            offset=0,
            limit=10000,  # Get all for filtering
        )

        # Decrypt and filter all entries
        filtered_entries = []
        for e in all_entries:
            decrypted_title = (
                decrypt_data(e.title, data_key) if e.title is not None else None
            )
            decrypted_content = decrypt_data(e.encrypted_content, data_key)

            # Search in title and content
            title_match = (
                decrypted_title and search_query in decrypted_title.lower()
                if decrypted_title
                else False
            )
            content_match = search_query in decrypted_content.lower()

            if title_match or content_match:
                filtered_entries.append(
                    {
                        "entry": e,
                        "decrypted_title": decrypted_title,
                        "decrypted_content": decrypted_content,
                    }
                )

        # Apply pagination to filtered results
        total = len(filtered_entries)
        offset = (page - 1) * per_page
        paginated_filtered = filtered_entries[offset : offset + per_page]

        # Build response entries
        response_entries = []
        for item in paginated_filtered:
            e = item["entry"]
            decrypted_title = item["decrypted_title"]
            decrypted_content = item["decrypted_content"]

            response_entries.append(
                EntryResponse(
                    id=e.id,
                    user_id=e.user_id,
                    title=decrypted_title,
                    content=decrypted_content,
                    summary=(
                        decrypt_data(e.encrypted_summary, data_key)
                        if e.encrypted_summary is not None
                        else None
                    ),
                    mood_rating=e.mood_rating,
                    tags=e.tags,
                    is_draft=e.is_draft,
                    created_at=e.created_at,
                    updated_at=e.updated_at,
                    ai_processed_at=e.ai_processed_at,
                )
            )

    total_pages = math.ceil(total / per_page) if per_page else 1

    return EntryListResponse(
        entries=response_entries,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{entry_id}", response_model=EntryResponse)
def get_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )

    data_key = get_user_data_key(session, user_id=current_user.id)
    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=decrypt_data(entry.title, data_key) if entry.title is not None else None,
        content=decrypt_data(entry.encrypted_content, data_key),
        summary=(
            decrypt_data(entry.encrypted_summary, data_key)
            if entry.encrypted_summary is not None
            else None
        ),
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        is_draft=entry.is_draft,
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
    session: Session = Depends(get_session),
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )

    # Only analyze if entry is not a draft and content was updated
    data_key = get_user_data_key(session, user_id=current_user.id)
    if entry_data.content is not None and not entry.is_draft:
        background_tasks.add_task(
            analyze_entry_background,
            entry.id,
            entry_data.content,
            current_user.id,
            data_key,
        )

    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=decrypt_data(entry.title, data_key) if entry.title is not None else None,
        content=decrypt_data(entry.encrypted_content, data_key),
        summary=(
            decrypt_data(entry.encrypted_summary, data_key)
            if entry.encrypted_summary is not None
            else None
        ),
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        is_draft=entry.is_draft,
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
    session: Session = Depends(get_session),
):
    """Partially update a diary entry (PATCH semantics)"""
    # Import encryption functions lazily
    from app.services.encryption_key_service import get_user_data_key
    from app.core.crypto import encrypt_data, decrypt_data

    # Get entry before updating to check if it was a draft
    existing_entry = entry_crud.get_entry_by_id(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
    )

    if existing_entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )

    was_draft = existing_entry.is_draft
    data_key = get_user_data_key(session, user_id=current_user.id)

    encrypted_content = None
    if entry_data.content is not None:
        encrypted_content = encrypt_data(entry_data.content, data_key)

    encrypted_title = None
    if entry_data.title is not None:
        encrypted_title = encrypt_data(entry_data.title, data_key)

    entry = entry_crud.update_entry(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
        title=encrypted_title,
        content=encrypted_content,
        tags=entry_data.tags,
        is_draft=entry_data.is_draft,
    )

    # Determine if we should trigger AI analysis
    should_analyze = False
    content_for_analysis = None

    # Case 1: Entry was changed from draft to non-draft
    if was_draft and entry_data.is_draft is False:
        should_analyze = True
        # Use updated content if provided, otherwise decrypt existing content
        if entry_data.content is not None:
            content_for_analysis = entry_data.content
        else:
            content_for_analysis = decrypt_data(
                existing_entry.encrypted_content, data_key
            )

    # Case 2: Content was updated and entry is not a draft
    elif entry_data.content is not None and not entry.is_draft:
        should_analyze = True
        content_for_analysis = entry_data.content

    if should_analyze and content_for_analysis:
        background_tasks.add_task(
            analyze_entry_background,
            entry.id,
            content_for_analysis,
            current_user.id,
            data_key,
        )

    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=decrypt_data(entry.title, data_key) if entry.title is not None else None,
        content=decrypt_data(entry.encrypted_content, data_key),
        summary=(
            decrypt_data(entry.encrypted_summary, data_key)
            if entry.encrypted_summary is not None
            else None
        ),
        mood_rating=entry.mood_rating,
        tags=entry.tags,
        is_draft=entry.is_draft,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        ai_processed_at=entry.ai_processed_at,
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete a diary entry"""
    entry = entry_crud.get_entry_by_id(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
    )

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found"
        )
    entry_crud.delete_entry(
        session,
        user_id=current_user.id,
        entry_id=entry_id,
    )

    return None


@router.post(
    "/from-audio", response_model=EntryResponse, status_code=status.HTTP_201_CREATED
)
async def create_entry_from_audio(
    audio_file: UploadFile = File(
        ..., description="Audio file to transcribe (MP3, WAV, etc.)"
    ),
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
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
            detail="Invalid audio file type. Supported formats: MP3, WAV, M4A, OGG, WEBM",
        )

    # Transcribe audio to text
    try:
        content = await audio_service.transcribe_audio(audio_file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}",
        )

    # Validate transcription result
    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No speech detected in audio file. Please check the audio quality.",
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
        summary=None,  # Will be set by background task
        tags=tags,
    )

    # Background AI analysis (sentiment + theme extraction)
    # Use asyncio.create_task for parallel execution since this endpoint is already async
    asyncio.create_task(
        analyze_entry_background(entry.id, content, current_user.id, data_key)
    )

    return EntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        title=title,
        content=content,
        summary=(
            decrypt_data(entry.encrypted_summary, data_key)
            if entry.encrypted_summary is not None
            else None
        ),
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
        print(f"Entry: {entry}")
        print(f"Entry is draft: {entry.is_draft}")
        if not entry:
            return

        if entry.is_draft:
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
