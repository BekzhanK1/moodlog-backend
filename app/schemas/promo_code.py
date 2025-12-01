"""
Schemas for promo code-related API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class PromoCodeCreateRequest(BaseModel):
    """Request schema for creating a promo code."""

    plan: str  # "pro_month" or "pro_year"
    code: Optional[str] = None  # Optional custom code (auto-generated if not provided)
    expires_at: Optional[datetime] = None  # Optional expiration date


class PromoCodeResponse(BaseModel):
    """Response schema for a promo code."""

    id: UUID
    code: str
    plan: str
    created_by: UUID
    used_by: Optional[UUID] = None
    used_at: Optional[datetime] = None
    is_used: bool
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PromoCodeListResponse(BaseModel):
    """Response schema for list of promo codes."""

    promo_codes: list[PromoCodeResponse]
    total: int


class PromoCodeRedeemRequest(BaseModel):
    """Request schema for redeeming a promo code."""

    code: str


class PromoCodeRedeemResponse(BaseModel):
    """Response schema for promo code redemption."""

    message: str
    plan: str
    expires_at: datetime
