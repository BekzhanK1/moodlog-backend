"""
CRUD operations for Payment model.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select
from app.models.payment import Payment


def create_payment(
    session: Session,
    *,
    user_id: UUID,
    amount: float,
    plan: str,
    currency: str = "KZT",
    webkassa_order_id: Optional[str] = None,
    status: str = "pending",
    payment_method: Optional[str] = None,
    payment_metadata: Optional[Dict[str, Any]] = None,
) -> Payment:
    """
    Create a new payment record.

    Args:
        session: Database session
        user_id: User ID
        amount: Payment amount
        plan: Plan identifier ("pro_month", "pro_year")
        currency: Currency code (default: "KZT")
        webkassa_order_id: Webkassa order ID (optional)
        status: Payment status (default: "pending")
        payment_method: Payment method (optional)
        payment_metadata: Additional metadata (optional)

    Returns:
        Created Payment instance
    """
    payment = Payment(
        user_id=user_id,
        amount=amount,
        currency=currency,
        plan=plan,
        webkassa_order_id=webkassa_order_id,
        status=status,
        payment_method=payment_method,
        payment_metadata=payment_metadata,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def get_payment_by_id(session: Session, *, payment_id: UUID) -> Optional[Payment]:
    """
    Get payment by ID.

    Args:
        session: Database session
        payment_id: Payment ID

    Returns:
        Payment instance or None
    """
    statement = select(Payment).where(Payment.id == payment_id)
    return session.exec(statement).first()


def get_payment_by_webkassa_order_id(
    session: Session, *, order_id: str
) -> Optional[Payment]:
    """
    Get payment by Webkassa order ID.

    Args:
        session: Database session
        order_id: Webkassa order ID

    Returns:
        Payment instance or None
    """
    statement = select(Payment).where(Payment.webkassa_order_id == order_id)
    return session.exec(statement).first()


def get_user_payments(
    session: Session, *, user_id: UUID, limit: Optional[int] = None
) -> List[Payment]:
    """
    Get all payments for a user, ordered by created_at descending.

    Args:
        session: Database session
        user_id: User ID
        limit: Optional limit on number of results

    Returns:
        List of Payment instances
    """
    statement = (
        select(Payment)
        .where(Payment.user_id == user_id)
        .order_by(Payment.created_at.desc())
    )
    if limit:
        statement = statement.limit(limit)
    return list(session.exec(statement).all())


def update_payment_status(
    session: Session,
    *,
    payment_id: UUID,
    status: str,
    webkassa_status: Optional[str] = None,
    webkassa_receipt_id: Optional[str] = None,
    subscription_id: Optional[UUID] = None,
    payment_metadata: Optional[Dict[str, Any]] = None,
) -> Optional[Payment]:
    """
    Update payment status and related fields.

    Args:
        session: Database session
        payment_id: Payment ID
        status: New payment status
        webkassa_status: Webkassa status (optional)
        webkassa_receipt_id: Webkassa receipt ID (optional)
        subscription_id: Associated subscription ID (optional)
        payment_metadata: Additional metadata (optional)

    Returns:
        Updated Payment instance or None
    """
    payment = get_payment_by_id(session, payment_id=payment_id)
    if not payment:
        return None

    payment.status = status
    if webkassa_status is not None:
        payment.webkassa_status = webkassa_status
    if webkassa_receipt_id is not None:
        payment.webkassa_receipt_id = webkassa_receipt_id
    if subscription_id is not None:
        payment.subscription_id = subscription_id
    if payment_metadata is not None:
        payment.payment_metadata = payment_metadata
    if status in ["completed", "failed", "refunded"]:
        payment.completed_at = datetime.utcnow()

    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment
