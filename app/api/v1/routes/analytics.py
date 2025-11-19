from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.services.analytics_service import analytics_service


router = APIRouter()


@router.get("/mood-trend")
def get_data_points_for_mood_trend(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    timezone_offset: Optional[int] = Query(
        None, description="Timezone offset in hours (e.g., 5 for UTC+5, -5 for UTC-5)"
    ),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return analytics_service.get_data_points_for_mood_trend(
        session,
        current_user.id,
        start_date,
        end_date,
        user_timezone_offset=timezone_offset,
    )


@router.get("/main-themes")
def get_main_themes(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return analytics_service.get_main_themes(
        session, current_user.id, start_date, end_date
    )


@router.get("/best-and-worst-day")
def get_best_and_worst_day(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return analytics_service.get_best_and_worst_entries_by_mood_rating(
        session, current_user.id, start_date, end_date
    )


@router.get("/compare-current-and-previous-month-mood-rating")
def compare_current_and_previous_month_mood_rating(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return analytics_service.compare_current_and_previous_month_mood_rating(
        session, current_user.id
    )
