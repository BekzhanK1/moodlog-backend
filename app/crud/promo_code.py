"""
CRUD operations for PromoCode model.
"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import secrets
import string
from sqlmodel import Session, select
from app.models.promo_code import PromoCode


def generate_promo_code(length: int = 12) -> str:
    """
    Generate a random promo code.

    Args:
        length: Length of the promo code (default: 12)

    Returns:
        Random promo code string (uppercase alphanumeric)
    """
    alphabet = string.ascii_uppercase + string.digits
    # Remove ambiguous characters (0, O, I, 1)
    alphabet = alphabet.replace("0", "").replace("O", "").replace("I", "").replace("1", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_promo_code(
    session: Session,
    *,
    code: Optional[str] = None,
    plan: str,
    created_by: UUID,
    expires_at: Optional[datetime] = None,
) -> PromoCode:
    """
    Create a new promo code.

    Args:
        session: Database session
        code: Promo code string (if None, will be auto-generated)
        plan: Plan identifier ("pro_month" or "pro_year")
        created_by: Admin user ID who created the code
        expires_at: Optional expiration date

    Returns:
        Created PromoCode instance
    """
    if code is None:
        # Generate unique code
        max_attempts = 10
        for _ in range(max_attempts):
            code = generate_promo_code()
            existing = get_promo_code_by_code(session, code=code)
            if not existing:
                break
        else:
            raise ValueError("Failed to generate unique promo code")

    promo_code = PromoCode(
        code=code.upper(),  # Store in uppercase
        plan=plan,
        created_by=created_by,
        expires_at=expires_at,
    )
    session.add(promo_code)
    session.commit()
    session.refresh(promo_code)
    return promo_code


def get_promo_code_by_code(session: Session, *, code: str) -> Optional[PromoCode]:
    """
    Get promo code by code string.

    Args:
        session: Database session
        code: Promo code string

    Returns:
        PromoCode instance or None
    """
    statement = select(PromoCode).where(PromoCode.code == code.upper())
    return session.exec(statement).first()


def get_promo_code_by_id(
    session: Session, *, promo_code_id: UUID
) -> Optional[PromoCode]:
    """
    Get promo code by ID.

    Args:
        session: Database session
        promo_code_id: Promo code ID

    Returns:
        PromoCode instance or None
    """
    statement = select(PromoCode).where(PromoCode.id == promo_code_id)
    return session.exec(statement).first()


def get_all_promo_codes(
    session: Session,
    *,
    include_used: bool = True,
    created_by: Optional[UUID] = None,
    limit: Optional[int] = None,
) -> List[PromoCode]:
    """
    Get all promo codes, optionally filtered.

    Args:
        session: Database session
        include_used: Whether to include used codes
        created_by: Filter by creator user ID
        limit: Optional limit on number of results

    Returns:
        List of PromoCode instances
    """
    statement = select(PromoCode)

    if not include_used:
        statement = statement.where(PromoCode.is_used == False)

    if created_by:
        statement = statement.where(PromoCode.created_by == created_by)

    statement = statement.order_by(PromoCode.created_at.desc())

    if limit:
        statement = statement.limit(limit)

    return list(session.exec(statement).all())


def redeem_promo_code(
    session: Session, *, promo_code: PromoCode, used_by: UUID
) -> PromoCode:
    """
    Mark a promo code as used.

    Args:
        session: Database session
        promo_code: PromoCode instance to redeem
        used_by: User ID who is redeeming the code

    Returns:
        Updated PromoCode instance

    Raises:
        ValueError: If code is already used or expired
    """
    if promo_code.is_used:
        raise ValueError("Promo code has already been used")

    if promo_code.expires_at and datetime.utcnow() > promo_code.expires_at:
        raise ValueError("Promo code has expired")

    promo_code.is_used = True
    promo_code.used_by = used_by
    promo_code.used_at = datetime.utcnow()

    session.add(promo_code)
    session.commit()
    session.refresh(promo_code)
    return promo_code

