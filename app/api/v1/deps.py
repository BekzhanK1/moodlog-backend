from fastapi import APIRouter
from app.api.v1.routes import auth, entries, analytics, insights

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(entries.router, prefix="/entries", tags=["diary entries"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
