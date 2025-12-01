"""
API routes for subscription management and payments.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import Dict, Any

from app.db.session import get_session
from app.models import User
from app.core.deps import get_current_user
from app.services.plan_service import (
    PLAN_CONFIG,
    get_plan_config,
    get_plan_price,
    is_plan_active,
)
from app.services.webkassa_service import webkassa_service
from app.crud import subscription as subscription_crud
from app.crud import payment as payment_crud
from app.schemas.subscription import (
    PlansListResponse,
    PlanResponse,
    SubscriptionResponse,
    StartTrialResponse,
    SubscribeRequest,
    SubscribeResponse,
    PaymentStatusResponse,
    WebkassaWebhookRequest,
)

router = APIRouter()


@router.get("/plans", response_model=PlansListResponse)
def get_available_plans():
    """
    Get all available subscription plans with features and pricing.
    """
    plans = [
        PlanResponse(
            id=plan_id,
            name=config["name"],
            price_monthly=config["price_monthly"],
            price_yearly=config["price_yearly"],
            duration_days=config["duration_days"],
            features=config["features"],
        )
        for plan_id, config in PLAN_CONFIG.items()
    ]
    return PlansListResponse(plans=plans)


@router.get("/current", response_model=SubscriptionResponse)
def get_current_subscription(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get current user's subscription status and features.
    """
    plan_config = get_plan_config(current_user.plan)
    return SubscriptionResponse(
        plan=current_user.plan,
        plan_name=plan_config["name"],
        status=current_user.subscription_status,
        started_at=current_user.plan_started_at,
        expires_at=current_user.plan_expires_at,
        trial_used=current_user.trial_used,
        features=plan_config["features"],
        is_active=is_plan_active(current_user),
    )


@router.post("/start-trial", response_model=StartTrialResponse)
def start_trial(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Start free trial for new users (14 days of Pro features).
    """
    if current_user.trial_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trial already used",
        )

    if current_user.plan != "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription",
        )

    # Set trial plan
    trial_duration = PLAN_CONFIG["trial"]["duration_days"]
    now = datetime.utcnow()

    current_user.plan = "trial"
    current_user.plan_started_at = now
    current_user.plan_expires_at = now + timedelta(days=trial_duration)
    current_user.trial_used = True
    current_user.subscription_status = "active"

    # Create subscription record
    subscription_crud.create_subscription(
        session,
        user_id=current_user.id,
        plan="trial",
        started_at=now,
        expires_at=current_user.plan_expires_at,
    )

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return StartTrialResponse(
        message="Trial started successfully",
        expires_at=current_user.plan_expires_at,
    )


@router.post("/subscribe", response_model=SubscribeResponse)
def initiate_subscription(
    request: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Initiate subscription payment via Webkassa.kz.
    Creates a payment record and returns payment URL for user to complete payment.
    """
    if request.plan not in ["pro_month", "pro_year"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Must be 'pro_month' or 'pro_year'",
        )

    plan_config = get_plan_config(request.plan)
    amount = get_plan_price(request.plan)

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan price",
        )

    # Generate unique order ID
    order_id = str(uuid4())

    # Create payment record
    payment = payment_crud.create_payment(
        session,
        user_id=current_user.id,
        amount=amount,
        plan=request.plan,
        webkassa_order_id=order_id,
        status="pending",
    )

    try:
        # Create payment order in Webkassa
        payment_response = webkassa_service.create_payment_order(
            amount=amount,
            user_email=current_user.email,
            plan_name=plan_config["name"],
            order_id=order_id,
        )

        # Update payment with webkassa response
        payment.webkassa_status = payment_response.get("status", "pending")
        payment.payment_metadata = payment_response
        session.add(payment)
        session.commit()
        session.refresh(payment)

        payment_url = payment_response.get("payment_url")
        if not payment_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get payment URL from Webkassa",
            )

        return SubscribeResponse(
            payment_id=payment.id,
            order_id=order_id,
            payment_url=payment_url,
            amount=amount,
        )

    except Exception as e:
        # Update payment status to failed
        payment.status = "failed"
        session.add(payment)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment order: {str(e)}",
        )


@router.post("/webhook/webkassa")
async def webkassa_webhook(
    webhook_data: WebkassaWebhookRequest,
    session: Session = Depends(get_session),
):
    """
    Webhook endpoint for Webkassa.kz payment notifications.
    This should be called by Webkassa when payment status changes.
    
    Note: In production, you should verify the webhook signature for security.
    """
    order_id = webhook_data.order_id
    payment_status = webhook_data.status

    # Find payment by order_id
    payment = payment_crud.get_payment_by_webkassa_order_id(
        session, order_id=order_id
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )

    # Update payment status
    payment.webkassa_status = payment_status
    payment.status = "completed" if payment_status == "success" else "failed"
    payment.completed_at = datetime.utcnow()

    if webhook_data.metadata:
        payment.payment_metadata = webhook_data.metadata

    if payment_status == "success":
        try:
            # Issue fiscal receipt
            receipt = webkassa_service.issue_fiscal_receipt(
                order_id=order_id,
                amount=payment.amount,
                user_email=payment.user.email,
            )
            payment.webkassa_receipt_id = receipt.get("receipt_id")

            # Activate subscription
            user = payment.user
            plan_config = get_plan_config(payment.plan)
            now = datetime.utcnow()

            user.plan = payment.plan
            user.plan_started_at = now
            user.plan_expires_at = now + timedelta(days=plan_config["duration_days"])
            user.subscription_status = "active"

            # Create subscription record
            subscription = subscription_crud.create_subscription(
                session,
                user_id=user.id,
                plan=payment.plan,
                started_at=now,
                expires_at=user.plan_expires_at,
            )
            payment.subscription_id = subscription.id

            session.add(user)
            session.add(payment)
            session.commit()

        except Exception as e:
            # Log error but don't fail the webhook
            # Payment is already marked as completed
            session.add(payment)
            session.commit()
            # In production, log this error for investigation
            print(f"Error processing successful payment: {e}")

    session.add(payment)
    session.commit()

    return {"status": "ok", "message": "Webhook processed successfully"}


@router.get("/payment/{payment_id}/status", response_model=PaymentStatusResponse)
def check_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Check payment status (polling endpoint for frontend).
    Optionally checks with Webkassa if payment is still pending.
    """
    try:
        payment_uuid = UUID(payment_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment ID"
        )

    payment = payment_crud.get_payment_by_id(session, payment_id=payment_uuid)
    if not payment or payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
        )

    # Optionally check with Webkassa if payment is still pending
    if payment.status == "pending" and payment.webkassa_order_id:
        try:
            status_response = webkassa_service.check_payment_status(
                payment.webkassa_order_id
            )
            webkassa_status = status_response.get("status")

            # Update payment if status changed
            if webkassa_status and webkassa_status != payment.webkassa_status:
                payment.webkassa_status = webkassa_status
                if webkassa_status == "success" and payment.status == "pending":
                    # Trigger the same logic as webhook
                    # For simplicity, we'll just update status here
                    # In production, you might want to call a shared function
                    payment.status = "completed"
                    payment.completed_at = datetime.utcnow()
                    session.add(payment)
                    session.commit()
                    session.refresh(payment)

        except Exception as e:
            # If Webkassa check fails, just return current status
            print(f"Error checking payment status with Webkassa: {e}")

    return PaymentStatusResponse(
        payment_id=payment.id,
        status=payment.status,
        webkassa_status=payment.webkassa_status,
        order_id=payment.webkassa_order_id,
    )

