from datetime import datetime, date
from typing import Optional, List, Tuple
from uuid import UUID

from sqlmodel import Session, select

from app.models import Insight


def get_insight_by_type_and_period(
    session: Session,
    *,
    user_id: UUID,
    type: str,
    period_key: str,
) -> Optional[Insight]:
    statement = select(Insight).where(
        Insight.user_id == user_id,
        Insight.type == type,
        Insight.period_key == period_key,
    )
    return session.exec(statement).first()


def create_or_update_insight(
    session: Session,
    *,
    user_id: UUID,
    type: str,
    period_key: str,
    period_label: str,
    content: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Insight:
    insight = get_insight_by_type_and_period(
        session, user_id=user_id, type=type, period_key=period_key
    )
    if insight is None:
        insight = Insight(
            user_id=user_id,
            type=type,
            period_key=period_key,
            period_label=period_label,
            start_date=start_date,
            end_date=end_date,
            encrypted_content=content,
        )
    else:
        insight.period_label = period_label
        insight.start_date = start_date
        insight.end_date = end_date
        insight.encrypted_content = content
        insight.updated_at = datetime.utcnow()

    session.add(insight)
    session.commit()
    session.refresh(insight)
    return insight


def list_insights(
    session: Session,
    *,
    user_id: UUID,
    type: Optional[str] = None,
    offset: int = 0,
    limit: int = 50,
) -> Tuple[List[Insight], int]:
    base = select(Insight).where(Insight.user_id == user_id)
    if type:
        base = base.where(Insight.type == type)
    count = len(session.exec(base).all())
    statement = base.order_by(
        Insight.created_at.desc()).offset(offset).limit(limit)
    items = session.exec(statement).all()
    return items, count
