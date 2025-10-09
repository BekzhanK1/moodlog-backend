from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
import os


# Create engine based on environment
engine = create_engine(
    settings.get_database_url,
    echo=settings.environment == "development",  # Log SQL queries in development
    connect_args={"check_same_thread": False} if "sqlite" in settings.get_database_url else {}
)


def create_db_and_tables():
    """Create database tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session

