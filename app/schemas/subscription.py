"""
Schemas for subscription-related API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PlanResponse(BaseModel):
    """Response schema for a subscription plan."""

    id: str
    name: str
    price_monthly: float
    price_yearly: float
    duration_days: Optional[int]
    features: Dict[str, Any]

    class Config:
        from_attributes = True


class PlansListResponse(BaseModel):
    """Response schema for list of available plans."""

    plans: list[PlanResponse]


class SubscriptionResponse(BaseModel):
    """Response schema for current user subscription."""

    plan: str
    plan_name: str
    status: str
    started_at: Optional[datetime]
    expires_at: Optional[datetime]
    trial_used: bool
    features: Dict[str, Any]
    is_active: bool

    class Config:
        from_attributes = True


class StartTrialResponse(BaseModel):
    """Response schema for starting a trial."""

    message: str
    expires_at: datetime


class SubscribeRequest(BaseModel):
    """Request schema for initiating a subscription."""

    plan: str  # "pro_month" or "pro_year"


class SubscribeResponse(BaseModel):
    """Response schema for subscription initiation."""

    payment_id: UUID
    order_id: str
    payment_url: str
    amount: float


class PaymentStatusResponse(BaseModel):
    """Response schema for payment status."""

    payment_id: UUID
    status: str
    webkassa_status: Optional[str]
    order_id: Optional[str]

    class Config:
        from_attributes = True


class WebkassaWebhookRequest(BaseModel):
    """Request schema for Webkassa.kz webhook."""

    order_id: str
    status: str
    amount: Optional[float] = None
    receipt_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
