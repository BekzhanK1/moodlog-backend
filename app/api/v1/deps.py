from fastapi import APIRouter
from app.api.v1.routes import auth, entries

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(entries.router, prefix="/entries", tags=["diary entries"])

