from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Optional
from uuid import UUID
from datetime import datetime
import math
from app.db.session import get_session
from app.models import User, Insight
from app.schemas import InsightResponse, InsightListResponse
from app.core.deps import get_current_user
from app.crud import insight as insight_crud
from app.services.ai_insights_service import ai_insights_service
from app.services.encryption_key_service import get_user_data_key
from app.core.crypto import decrypt_data

router = APIRouter()


@router.post(
    "/monthly", response_model=InsightResponse, status_code=status.HTTP_201_CREATED
)
def generate_monthly_insights(
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
    month: Optional[int] = Query(
        None, description="Month 1-12 (defaults to current month)"
    ),
    use_pro_model: bool = Query(True, description="Use GPT-4o instead of GPT-4o-mini"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Generate monthly insights report for a specific month"""
    insights_text = ai_insights_service.generate_monthly_insights_report(
        session=session,
        user_id=current_user.id,
        target_year=year,
        target_month=month,
        use_pro_model=use_pro_model,
    )

    if not insights_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entries found for the specified month",
        )

    # Get the saved insight to return
    now = datetime.now()
    target_year = year or now.year
    target_month = month or now.month
    period_key = f"{target_year}-{target_month:02d}"

    insight = insight_crud.get_insight_by_type_and_period(
        session=session,
        user_id=current_user.id,
        type="monthly",
        period_key=period_key,
    )

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Insight was generated but could not be retrieved",
        )

    # Decrypt content
    data_key = get_user_data_key(session, user_id=current_user.id)
    decrypted_content = decrypt_data(insight.encrypted_content, data_key)

    return InsightResponse(
        id=insight.id,
        user_id=insight.user_id,
        type=insight.type,
        period_key=insight.period_key,
        period_label=insight.period_label,
        content=decrypted_content,
        start_date=insight.start_date,
        end_date=insight.end_date,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


@router.get("/monthly", response_model=InsightResponse)
def get_monthly_insights(
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
    month: Optional[int] = Query(
        None, description="Month 1-12 (defaults to current month)"
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get existing monthly insights report for a specific month"""
    now = datetime.now()
    target_year = year or now.year
    target_month = month or now.month
    period_key = f"{target_year}-{target_month:02d}"

    insight = insight_crud.get_insight_by_type_and_period(
        session=session,
        user_id=current_user.id,
        type="monthly",
        period_key=period_key,
    )

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monthly insights not found for the specified month",
        )

    # Decrypt content
    data_key = get_user_data_key(session, user_id=current_user.id)
    decrypted_content = decrypt_data(insight.encrypted_content, data_key)

    return InsightResponse(
        id=insight.id,
        user_id=insight.user_id,
        type=insight.type,
        period_key=insight.period_key,
        period_label=insight.period_label,
        content=decrypted_content,
        start_date=insight.start_date,
        end_date=insight.end_date,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


@router.post(
    "/weekly", response_model=InsightResponse, status_code=status.HTTP_201_CREATED
)
def generate_weekly_insights(
    iso_year: Optional[int] = Query(
        None, description="ISO year (defaults to current ISO year)"
    ),
    iso_week: Optional[int] = Query(
        None, description="ISO week number 1-53 (defaults to current ISO week)"
    ),
    use_pro_model: bool = Query(True, description="Use GPT-4o instead of GPT-4o-mini"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Generate weekly insights report for a specific ISO year/week"""
    insights_text = ai_insights_service.generate_weekly_insights_report(
        session=session,
        user_id=current_user.id,
        iso_year=iso_year,
        iso_week=iso_week,
        use_pro_model=use_pro_model,
    )

    if not insights_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No entries found for the specified ISO week",
        )

    # Get the saved insight to return
    now = datetime.now()
    target_iso = now.isocalendar()
    target_year = iso_year or target_iso.year
    target_week = iso_week or target_iso.week
    period_key = f"{target_year}-W{target_week:02d}"

    insight = insight_crud.get_insight_by_type_and_period(
        session=session,
        user_id=current_user.id,
        type="weekly",
        period_key=period_key,
    )

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Insight was generated but could not be retrieved",
        )

    # Decrypt content
    data_key = get_user_data_key(session, user_id=current_user.id)
    decrypted_content = decrypt_data(insight.encrypted_content, data_key)

    return InsightResponse(
        id=insight.id,
        user_id=insight.user_id,
        type=insight.type,
        period_key=insight.period_key,
        period_label=insight.period_label,
        content=decrypted_content,
        start_date=insight.start_date,
        end_date=insight.end_date,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


@router.get("/weekly", response_model=InsightResponse)
def get_weekly_insights(
    iso_year: Optional[int] = Query(
        None, description="ISO year (defaults to current ISO year)"
    ),
    iso_week: Optional[int] = Query(
        None, description="ISO week number 1-53 (defaults to current ISO week)"
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get existing weekly insights report for a specific ISO year/week"""
    now = datetime.now()
    target_iso = now.isocalendar()
    target_year = iso_year or target_iso.year
    target_week = iso_week or target_iso.week
    period_key = f"{target_year}-W{target_week:02d}"

    insight = insight_crud.get_insight_by_type_and_period(
        session=session,
        user_id=current_user.id,
        type="weekly",
        period_key=period_key,
    )

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weekly insights not found for the specified ISO week",
        )

    # Decrypt content
    data_key = get_user_data_key(session, user_id=current_user.id)
    decrypted_content = decrypt_data(insight.encrypted_content, data_key)

    return InsightResponse(
        id=insight.id,
        user_id=insight.user_id,
        type=insight.type,
        period_key=insight.period_key,
        period_label=insight.period_label,
        content=decrypted_content,
        start_date=insight.start_date,
        end_date=insight.end_date,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


@router.get("/", response_model=InsightListResponse)
def list_insights(
    type: Optional[str] = Query(
        None, description="Filter by insight type (monthly, weekly, specific, custom)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List all insights for the current user"""
    offset = (page - 1) * per_page
    insights, total = insight_crud.list_insights(
        session=session,
        user_id=current_user.id,
        type=type,
        offset=offset,
        limit=per_page,
    )

    # Decrypt all insights
    data_key = get_user_data_key(session, user_id=current_user.id)
    response_insights = [
        InsightResponse(
            id=i.id,
            user_id=i.user_id,
            type=i.type,
            period_key=i.period_key,
            period_label=i.period_label,
            content=decrypt_data(i.encrypted_content, data_key),
            start_date=i.start_date,
            end_date=i.end_date,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in insights
    ]

    total_pages = math.ceil(total / per_page) if total > 0 else 0

    return InsightListResponse(
        insights=response_insights,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{insight_id}", response_model=InsightResponse)
def get_insight(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get a specific insight by ID"""
    from sqlmodel import select

    statement = select(Insight).where(
        Insight.id == insight_id, Insight.user_id == current_user.id
    )
    insight = session.exec(statement).first()

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found"
        )

    # Decrypt content
    data_key = get_user_data_key(session, user_id=current_user.id)
    decrypted_content = decrypt_data(insight.encrypted_content, data_key)

    return InsightResponse(
        id=insight.id,
        user_id=insight.user_id,
        type=insight.type,
        period_key=insight.period_key,
        period_label=insight.period_label,
        content=decrypted_content,
        start_date=insight.start_date,
        end_date=insight.end_date,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )
