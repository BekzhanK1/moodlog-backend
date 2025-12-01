"""
CRUD operations for Subscription model.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select
from app.models.subscription import Subscription


def create_subscription(
    session: Session,
    *,
    user_id: UUID,
    plan: str,
    started_at: datetime,
    expires_at: Optional[datetime] = None,
    status: str = "active",
) -> Subscription:
    """
    Create a new subscription record.

    Args:
        session: Database session
        user_id: User ID
        plan: Plan identifier ("free", "trial", "pro_month", "pro_year")
        started_at: Subscription start date
        expires_at: Subscription expiration date (optional)
        status: Subscription status ("active", "expired", "cancelled", "pending")

    Returns:
        Created Subscription instance
    """
    subscription = Subscription(
        user_id=user_id,
        plan=plan,
        status=status,
        started_at=started_at,
        expires_at=expires_at,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def get_subscription_by_id(
    session: Session, *, subscription_id: UUID
) -> Optional[Subscription]:
    """
    Get subscription by ID.

    Args:
        session: Database session
        subscription_id: Subscription ID

    Returns:
        Subscription instance or None
    """
    statement = select(Subscription).where(Subscription.id == subscription_id)
    return session.exec(statement).first()


def get_user_subscriptions(
    session: Session, *, user_id: UUID, limit: Optional[int] = None
) -> List[Subscription]:
    """
    Get all subscriptions for a user, ordered by created_at descending.

    Args:
        session: Database session
        user_id: User ID
        limit: Optional limit on number of results

    Returns:
        List of Subscription instances
    """
    statement = (
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.created_at.desc())
    )
    if limit:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


def get_active_subscription(
    session: Session, *, user_id: UUID
) -> Optional[Subscription]:
    """
    Get the active subscription for a user.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Active Subscription instance or None
    """
    statement = (
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
    )
    return session.exec(statement).first()


def cancel_subscription(
    session: Session, *, subscription_id: UUID
) -> Optional[Subscription]:
    """
    Cancel a subscription.

    Args:
        session: Database session
        subscription_id: Subscription ID

    Returns:
        Updated Subscription instance or None
    """
    subscription = get_subscription_by_id(session, subscription_id=subscription_id)
    if not subscription:
        return None

    subscription.status = "cancelled"
    subscription.cancelled_at = datetime.utcnow()
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def expire_subscription(
    session: Session, *, subscription_id: UUID
) -> Optional[Subscription]:
    """
    Mark a subscription as expired.

    Args:
        session: Database session
        subscription_id: Subscription ID

    Returns:
        Updated Subscription instance or None
    """
    subscription = get_subscription_by_id(session, subscription_id=subscription_id)
    if not subscription:
        return None

    subscription.status = "expired"
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription
