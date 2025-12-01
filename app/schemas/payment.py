"""
Schemas for payment-related API requests and responses.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PaymentResponse(BaseModel):
    """Response schema for a payment record."""

    id: UUID
    user_id: UUID
    subscription_id: Optional[UUID]
    amount: float
    currency: str
    plan: str
    status: str
    webkassa_order_id: Optional[str]
    webkassa_receipt_id: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Response schema for list of payments."""

    payments: list[PaymentResponse]
    total: int

