from dotenv import load_dotenv
from typing import Optional
import os

# Load environment variables from .env file
load_dotenv()


class Settings:
    def __init__(self):
        # Database settings
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./moodlog.db")
        self.database_url_prod: Optional[str] = os.getenv("DATABASE_URL_PROD")

        # JWT settings
        self.secret_key: str = os.getenv(
            "SECRET_KEY", "your-secret-key-change-in-production"
        )
        self.algorithm: str = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )

        # CORS settings
        self.frontend_origin: str = os.getenv(
            "FRONTEND_ORIGIN", "http://localhost:3000"
        )

        # Environment
        self.environment: str = os.getenv("ENVIRONMENT", "development")

        self.master_encryption_key: str = os.getenv(
            "MASTER_ENCRYPTION_KEY", "your-master-encryption-key-change-in-production"
        )
        self.hf_token: str = os.getenv("HF_TOKEN", "your-huggingface-token")
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

        # GOOGLE AUTH
        self.google_client_id: str = os.getenv(
            "GOOGLE_CLIENT_ID", "your-google-client-id"
        )
        self.google_client_secret: str = os.getenv(
            "GOOGLE_CLIENT_SECRET", "your-google-client-secret"
        )
        self.google_redirect_uri: str = os.getenv(
            "GOOGLE_REDIRECT_URI", "your-google-redirect-uri"
        )

    @property
    def get_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        if self.environment == "production" and self.database_url_prod:
            return self.database_url_prod
        return self.database_url


# Global settings instance
settings = Settings()
