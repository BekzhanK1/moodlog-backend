from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import create_db_and_tables
from app.api.v1.deps import api_router
from datetime import datetime
from pathlib import Path

# Create FastAPI app
app = FastAPI(
    title="MoodLog API",
    description="A personal mood journal and diary web application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(api_router, prefix="/v1")

# Setup templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    create_db_and_tables()


@app.get("/health", response_class=HTMLResponse)
def health_check(request: Request):
    """Health check endpoint with modern HTML response"""
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    return templates.TemplateResponse(
        "health.html",
        {
            "request": request,
            "current_time": current_time,
            "version": "1.0.0",
        },
    )


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "Welcome to MoodLog API", "version": "1.0.0", "docs": "/docs"}
