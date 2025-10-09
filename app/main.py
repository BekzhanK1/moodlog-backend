from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import create_db_and_tables
from app.api.v1.deps import api_router

# Create FastAPI app
app = FastAPI(
    title="MoodLog API",
    description="A personal mood journal and diary web application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    create_db_and_tables()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to MoodLog API",
        "version": "1.0.0",
        "docs": "/docs"
    }

