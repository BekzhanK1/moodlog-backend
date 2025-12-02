from datetime import date, timedelta
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func

from app.db.session import get_session
from app.core.deps import require_admin
from app.models import User, Entry
from app.models.payment import Payment


router = APIRouter()


@router.get("/admin/metrics/engagement")
def get_engagement_metrics(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    High-level engagement metrics for admins:
    - total_users: total registered users
    - dau: daily active users today (at least one non-draft entry)
    - wau: weekly active users (last 7 days)
    - mau: monthly active users (last 30 days)
    - avg_entries_per_active_user_30d: average entries per active user in last 30 days
    """

    today = date.today()
    seven_days_ago = today - timedelta(days=6)
    thirty_days_ago = today - timedelta(days=29)

    # Total users
    total_users = session.exec(select(func.count(User.id))).one()

    # Active users in different windows (non-draft entries)
    dau = session.exec(
        select(func.count(func.distinct(Entry.user_id))).where(
            Entry.is_draft == False,  # noqa: E712
            func.date(Entry.created_at) == today,
        )
    ).one()

    wau = session.exec(
        select(func.count(func.distinct(Entry.user_id))).where(
            Entry.is_draft == False,  # noqa: E712
            func.date(Entry.created_at) >= seven_days_ago,
        )
    ).one()

    mau = session.exec(
        select(func.count(func.distinct(Entry.user_id))).where(
            Entry.is_draft == False,  # noqa: E712
            func.date(Entry.created_at) >= thirty_days_ago,
        )
    ).one()

    # Average entries per active user in last 30 days
    total_entries_30d, active_users_30d = session.exec(
        select(
            func.count(Entry.id),
            func.count(func.distinct(Entry.user_id)),
        ).where(
            Entry.is_draft == False,  # noqa: E712
            func.date(Entry.created_at) >= thirty_days_ago,
        )
    ).one()

    avg_entries_per_active_user_30d = (
        float(total_entries_30d) / active_users_30d if active_users_30d else 0.0
    )

    return {
        "total_users": total_users,
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "avg_entries_per_active_user_30d": avg_entries_per_active_user_30d,
    }


@router.get("/admin/metrics/mood")
def get_mood_metrics(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Mood/outcome metrics for admins:
    - avg_mood_30d: average mood rating in last 30 days (all users)
    - avg_mood_all_time: average mood rating across all time
    - entries_with_mood_ratio: share of entries that have mood_rating
    """

    today = date.today()
    thirty_days_ago = today - timedelta(days=29)

    # All-time mood
    avg_mood_all_time = session.exec(
        select(func.avg(Entry.mood_rating)).where(
            Entry.is_draft == False,  # noqa: E712
            Entry.mood_rating.is_not(None),
        )
    ).one()

    # 30-day mood
    avg_mood_30d = session.exec(
        select(func.avg(Entry.mood_rating)).where(
            Entry.is_draft == False,  # noqa: E712
            Entry.mood_rating.is_not(None),
            func.date(Entry.created_at) >= thirty_days_ago,
        )
    ).one()

    # Coverage: how many entries have mood_rating
    total_entries = session.exec(
        select(func.count(Entry.id)).where(Entry.is_draft == False)  # noqa: E712
    ).one()

    entries_with_mood = session.exec(
        select(func.count(Entry.id)).where(
            Entry.is_draft == False,  # noqa: E712
            Entry.mood_rating.is_not(None),
        )
    ).one()

    entries_with_mood_ratio = (
        float(entries_with_mood) / total_entries if total_entries else 0.0
    )

    return {
        "avg_mood_all_time": float(avg_mood_all_time) if avg_mood_all_time else None,
        "avg_mood_30d": float(avg_mood_30d) if avg_mood_30d else None,
        "entries_with_mood_ratio": entries_with_mood_ratio,
    }


@router.get("/admin/metrics/engagement/history")
def get_engagement_history(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """
    Daily engagement history for the last N days.

    Returns an array of points:
    - date: ISO date string (YYYY-MM-DD)
    - dau: daily active users (non-draft entries)
    - new_users: users registered that day
    """

    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # DAU per day
    dau_rows = session.exec(
        select(
            func.date(Entry.created_at).label("day"),
            func.count(func.distinct(Entry.user_id)).label("dau"),
        )
        .where(
            Entry.is_draft == False,  # noqa: E712
            func.date(Entry.created_at) >= start_date,
        )
        .group_by("day")
        .order_by("day")
    ).all()

    # New users per day
    new_user_rows = session.exec(
        select(
            func.date(User.created_at).label("day"),
            func.count(User.id).label("new_users"),
        )
        .where(func.date(User.created_at) >= start_date)
        .group_by("day")
        .order_by("day")
    ).all()

    # Merge into dict keyed by ISO date string
    data: Dict[str, Dict[str, Any]] = {}

    for day, dau in dau_rows:
        day_str = day if isinstance(day, str) else day.isoformat()
        data.setdefault(day_str, {"date": day_str, "dau": 0, "new_users": 0})
        data[day_str]["dau"] = dau

    for day, new_users in new_user_rows:
        day_str = day if isinstance(day, str) else day.isoformat()
        data.setdefault(day_str, {"date": day_str, "dau": 0, "new_users": 0})
        data[day_str]["new_users"] = new_users

    # Ensure continuous range (fill missing days with zeros)
    result: List[Dict[str, Any]] = []
    current = start_date
    while current <= today:
        current_str = current.isoformat()
        if current_str not in data:
            result.append(
                {
                    "date": current_str,
                    "dau": 0,
                    "new_users": 0,
                }
            )
        else:
            result.append(data[current_str])
        current += timedelta(days=1)

    return result


@router.get("/admin/metrics/mood/history")
def get_mood_history(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """
    Daily mood history for the last N days.

    Returns an array of points:
    - date: ISO date string (YYYY-MM-DD)
    - avg_mood: average mood_rating that day (non-draft entries)
    - entries_with_mood: number of entries with mood_rating that day
    """

    today = date.today()
    start_date = today - timedelta(days=days - 1)

    rows = session.exec(
        select(
            func.date(Entry.created_at).label("day"),
            func.avg(Entry.mood_rating).label("avg_mood"),
            func.count(Entry.id).label("entries_with_mood"),
        )
        .where(
            Entry.is_draft == False,  # noqa: E712
            Entry.mood_rating.is_not(None),
            func.date(Entry.created_at) >= start_date,
        )
        .group_by("day")
        .order_by("day")
    ).all()

    data: Dict[str, Dict[str, Any]] = {}
    for day, avg_mood, entries_with_mood in rows:
        day_str = day if isinstance(day, str) else day.isoformat()
        data[day_str] = {
            "date": day_str,
            "avg_mood": float(avg_mood) if avg_mood is not None else None,
            "entries_with_mood": entries_with_mood,
        }

    # Fill missing days
    result: List[Dict[str, Any]] = []
    current = start_date
    while current <= today:
        current_str = current.isoformat()
        if current_str not in data:
            result.append(
                {
                    "date": current_str,
                    "avg_mood": None,
                    "entries_with_mood": 0,
                }
            )
        else:
            result.append(data[current_str])
        current += timedelta(days=1)

    return result


@router.get("/admin/metrics/revenue/history")
def get_revenue_history(
    days: int = Query(90, ge=1, le=365),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """
    Daily revenue history for the last N days.

    Returns an array of points:
    - date: ISO date string (YYYY-MM-DD)
    - total_revenue: sum of completed payments that day
    - payments_count: number of completed payments that day
    """

    today = date.today()
    start_date = today - timedelta(days=days - 1)

    rows = session.exec(
        select(
            func.date(Payment.completed_at).label("day"),
            func.coalesce(func.sum(Payment.amount), 0.0).label("total_revenue"),
            func.count(Payment.id).label("payments_count"),
        )
        .where(
            Payment.status == "completed",
            Payment.completed_at.is_not(None),
            func.date(Payment.completed_at) >= start_date,
        )
        .group_by("day")
        .order_by("day")
    ).all()

    data: Dict[str, Dict[str, Any]] = {}
    for day, total_revenue, payments_count in rows:
        day_str = day if isinstance(day, str) else day.isoformat()
        data[day_str] = {
            "date": day_str,
            "total_revenue": float(total_revenue),
            "payments_count": payments_count,
        }

    # Fill missing days
    result: List[Dict[str, Any]] = []
    current = start_date
    while current <= today:
        current_str = current.isoformat()
        if current_str not in data:
            result.append(
                {
                    "date": current_str,
                    "total_revenue": 0.0,
                    "payments_count": 0,
                }
            )
        else:
            result.append(data[current_str])
        current += timedelta(days=1)

    return result


@router.get("/admin/metrics/revenue")
def get_revenue_metrics(
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Simple revenue metrics based on Payment model:
    - total_revenue: sum of completed payments all time
    - mrr_estimate: naive MRR estimate based on active pro_month / pro_year subscriptions
      (uses plan field on User and latest completed payments)
    """

    # All-time completed revenue
    total_revenue = session.exec(
        select(func.coalesce(func.sum(Payment.amount), 0.0)).where(
            Payment.status == "completed"
        )
    ).one()

    # Count current Pro users by plan
    pro_month_users = session.exec(
        select(func.count(User.id)).where(User.plan == "pro_month")
    ).one()
    pro_year_users = session.exec(
        select(func.count(User.id)).where(User.plan == "pro_year")
    ).one()

    # Average ticket sizes for month/year based on completed payments
    avg_month_payment = session.exec(
        select(func.avg(Payment.amount)).where(
            Payment.status == "completed", Payment.plan == "pro_month"
        )
    ).one()
    avg_year_payment = session.exec(
        select(func.avg(Payment.amount)).where(
            Payment.status == "completed", Payment.plan == "pro_year"
        )
    ).one()

    avg_month_payment = float(avg_month_payment) if avg_month_payment else 0.0
    avg_year_payment = float(avg_year_payment) if avg_year_payment else 0.0

    # Naive MRR: monthly payments + 1/12 of yearly payments
    mrr_estimate = pro_month_users * avg_month_payment + pro_year_users * (
        avg_year_payment / 12.0 if avg_year_payment else 0.0
    )

    return {
        "total_revenue": float(total_revenue) if total_revenue is not None else 0.0,
        "pro_month_users": pro_month_users,
        "pro_year_users": pro_year_users,
        "avg_month_payment": avg_month_payment,
        "avg_year_payment": avg_year_payment,
        "mrr_estimate": mrr_estimate,
    }
