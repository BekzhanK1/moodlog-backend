from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database settings
    database_url: str = "sqlite:///./moodlog.db"
    database_url_prod: Optional[str] = None
    
    # JWT settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS settings
    frontend_origin: str = "http://localhost:3000"
    
    # Environment
    environment: str = "development"

    master_encryption_key: str = "your-master-encryption-key-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        if self.environment == "production" and self.database_url_prod:
            return self.database_url_prod
        return self.database_url


# Global settings instance
settings = Settings()

