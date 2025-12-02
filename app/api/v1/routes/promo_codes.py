"""
API routes for promo code management (admin) and redemption (users).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from datetime import datetime, timedelta
from typing import Optional

from app.db.session import get_session
from app.models import User
from app.core.deps import get_current_user, require_admin
from app.services.plan_service import get_plan_config
from app.crud import promo_code as promo_code_crud
from app.crud import subscription as subscription_crud
from app.schemas.promo_code import (
    PromoCodeCreateRequest,
    PromoCodeResponse,
    PromoCodeListResponse,
    PromoCodeRedeemRequest,
    PromoCodeRedeemResponse,
)

router = APIRouter()


@router.post(
    "/admin/promo-codes",
    response_model=PromoCodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_promo_code(
    request: PromoCodeCreateRequest,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """
    Create a new promo code (Admin only).
    """
    if request.plan not in ["pro_month", "pro_year"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Must be 'pro_month' or 'pro_year'",
        )

    # Validate custom code if provided
    if request.code:
        request.code = request.code.upper().strip()
        if len(request.code) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Promo code must be at least 6 characters",
            )
        # Check if code already exists
        existing = promo_code_crud.get_promo_code_by_code(session, code=request.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Promo code already exists",
            )

    if request.max_uses <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_uses must be at least 1",
        )

    try:
        promo_code = promo_code_crud.create_promo_code(
            session,
            code=request.code,
            plan=request.plan,
            created_by=current_user.id,
            expires_at=request.expires_at,
            max_uses=request.max_uses,
        )
        return PromoCodeResponse(
            id=promo_code.id,
            code=promo_code.code,
            plan=promo_code.plan,
            created_by=promo_code.created_by,
            max_uses=promo_code.max_uses,
            uses_count=promo_code.uses_count,
            used_by=promo_code.used_by,
            used_at=promo_code.used_at,
            is_used=promo_code.is_used,
            created_at=promo_code.created_at,
            expires_at=promo_code.expires_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/admin/promo-codes", response_model=PromoCodeListResponse)
def list_promo_codes(
    include_used: bool = Query(True, description="Include used promo codes"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit results"),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """
    List all promo codes (Admin only).
    """
    promo_codes = promo_code_crud.get_all_promo_codes(
        session,
        include_used=include_used,
        created_by=current_user.id,
        limit=limit,
    )

    return PromoCodeListResponse(
        promo_codes=[
            PromoCodeResponse(
                id=pc.id,
                code=pc.code,
                plan=pc.plan,
                created_by=pc.created_by,
                max_uses=pc.max_uses,
                uses_count=pc.uses_count,
                used_by=pc.used_by,
                used_at=pc.used_at,
                is_used=pc.is_used,
                created_at=pc.created_at,
                expires_at=pc.expires_at,
            )
            for pc in promo_codes
        ],
        total=len(promo_codes),
    )


@router.delete(
    "/admin/promo-codes/{promo_code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_promo_code(
    promo_code_id: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    """
    Delete a promo code by ID (Admin only).
    """
    # Validate UUID format
    from uuid import UUID

    try:
        promo_code_uuid = UUID(promo_code_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid promo code ID"
        )

    deleted = promo_code_crud.delete_promo_code(session, promo_code_id=promo_code_uuid)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found"
        )

    return None


@router.post("/promo-codes/redeem", response_model=PromoCodeRedeemResponse)
def redeem_promo_code(
    request: PromoCodeRedeemRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Redeem a promo code to get a subscription plan.
    User must have 'free' or 'trial' plan to redeem.
    """
    # Validate user can redeem (must have free or trial plan)
    if current_user.plan not in ["free", "trial"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only redeem promo codes if you have a Free or Trial plan. Please cancel your current subscription first.",
        )

    # Find promo code
    promo_code = promo_code_crud.get_promo_code_by_code(session, code=request.code)
    if not promo_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found",
        )

    # Check if already used
    if promo_code.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This promo code has already been used",
        )

    # Check if expired
    if promo_code.expires_at and datetime.utcnow() > promo_code.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This promo code has expired",
        )

    try:
        # Redeem the code
        promo_code_crud.redeem_promo_code(
            session, promo_code=promo_code, used_by=current_user.id
        )

        # Activate subscription for user
        plan_config = get_plan_config(promo_code.plan)
        now = datetime.utcnow()

        current_user.plan = promo_code.plan
        current_user.plan_started_at = now
        current_user.plan_expires_at = now + timedelta(
            days=plan_config["duration_days"]
        )
        current_user.subscription_status = "active"

        # Create subscription record
        subscription_crud.create_subscription(
            session,
            user_id=current_user.id,
            plan=promo_code.plan,
            started_at=now,
            expires_at=current_user.plan_expires_at,
        )

        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        return PromoCodeRedeemResponse(
            message="Promo code redeemed successfully! Your subscription has been activated.",
            plan=promo_code.plan,
            expires_at=current_user.plan_expires_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
