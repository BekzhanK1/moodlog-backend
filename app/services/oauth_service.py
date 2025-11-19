from typing import Optional, Dict, Any, Tuple
from authlib.integrations.requests_client import OAuth2Session
from app.core.config import settings
import httpx


class GoogleOAuthService:
    """Service for handling Google OAuth authentication"""

    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.authorization_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.scope = "openid email profile"

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate the Google OAuth authorization URL

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Tuple of (authorization_url, state)
        """
        oauth_client = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )

        authorization_url, state = oauth_client.create_authorization_url(
            self.authorization_base_url, state=state
        )

        return authorization_url, state

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from Google callback

        Returns:
            Dictionary containing token information
        """
        oauth_client = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        )

        token = oauth_client.fetch_token(url=self.token_url, code=code)

        return token

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google using access token

        Args:
            access_token: OAuth access token

        Returns:
            Dictionary containing user information (id, email, name, picture, etc.)
        """
        with httpx.Client() as client:
            response = client.get(
                self.userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()

    def authenticate_user(self, code: str) -> Dict[str, Any]:
        """
        Complete OAuth flow: exchange code for token and get user info

        Args:
            code: Authorization code from Google callback

        Returns:
            Dictionary containing both token and user information
        """
        # Exchange code for token
        token = self.exchange_code_for_token(code)

        # Get user info
        user_info = self.get_user_info(token["access_token"])

        return {"token": token, "user_info": user_info}


# Global instance
google_oauth_service = GoogleOAuthService()
