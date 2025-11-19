import secrets
import urllib.parse
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from app.db.session import get_session
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse, Token
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.core.deps import get_current_user
from datetime import timedelta
from app.core.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.crud import user as user_crud
from app.services.encryption_key_service import create_and_store_wrapped_key
from app.services.oauth_service import google_oauth_service

router = APIRouter()
refresh_security = HTTPBearer()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    """Register a new user"""
    # Check if user already exists
    existing_user = user_crud.get_user_by_email(session, email=user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = user_crud.create_user(
        session,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    # Generate and persist per-user encryption key (wrapped by master key)
    create_and_store_wrapped_key(session, user_id=user.id)

    return user


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, session: Session = Depends(get_session)):
    """Login user and return JWT tokens"""
    # Find user by email
    user = user_crud.get_user_by_email(session, email=user_credentials.email)

    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(refresh_security),
):
    """Exchange a refresh token for a new access token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(credentials.credentials, credentials_exception)
    # Issue new access token; keep refresh as-is (client can keep reusing until it expires)
    access_token = create_access_token(data={"sub": str(token_data.user_id)})
    return {
        "access_token": access_token,
        "refresh_token": credentials.credentials,
        "token_type": "bearer",
        "expires_in": int(
            timedelta(minutes=settings.access_token_expire_minutes).total_seconds()
        ),
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.get("/google/login")
def google_login():
    """Redirect to Google OAuth login page"""
    state = secrets.token_urlsafe(32)
    authorization_url, _ = google_oauth_service.get_authorization_url(state=state)
    print(authorization_url)
    if not authorization_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate authorization URL",
        )
    return RedirectResponse(url=authorization_url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
def google_callback(
    code: str, state: Optional[str] = None, session: Session = Depends(get_session)
):
    """Complete Google OAuth flow and redirect to frontend with tokens"""

    try:
        oauth_data = google_oauth_service.authenticate_user(code=code)
        user_info = oauth_data["user_info"]

        user = user_crud.create_user_from_google_user(
            session,
            google_id=user_info["id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info["picture"],
        )

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Redirect to frontend with tokens in URL hash
        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
        }
        token_params = urllib.parse.urlencode(tokens)
        frontend_url = f"{settings.frontend_origin}/auth/callback#{token_params}"

        return RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)

    except Exception as e:
        # Redirect to frontend with error
        error_param = urllib.parse.urlencode({"error": str(e)})
        frontend_url = f"{settings.frontend_origin}/auth/callback?{error_param}"
        return RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)
