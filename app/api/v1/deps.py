from fastapi import APIRouter
from app.api.v1.routes import (
    auth,
    entries,
    analytics,
    insights,
    subscriptions,
    promo_codes,
    admin_metrics,
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(entries.router, prefix="/entries", tags=["diary entries"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(
    subscriptions.router, prefix="/subscriptions", tags=["subscriptions"]
)
api_router.include_router(promo_codes.router, prefix="", tags=["promo codes"])
api_router.include_router(admin_metrics.router, prefix="", tags=["admin metrics"])
