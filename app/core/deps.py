"""
Dependencies for FastAPI routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from app.db.session import get_session
from app.models import User
from app.core.security import verify_token
from app.crud import user as user_crud
from app.services.plan_service import can_use_feature, is_plan_active

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        session: Database session

    Returns:
        User instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    token_data = verify_token(token, credentials_exception)
    user_id = token_data.user_id

    user = user_crud.get_user_by_id(session, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_pro_feature(feature: str):
    """
    Dependency factory to require a Pro feature.

    Usage:
        @router.get("/some-endpoint")
        def some_endpoint(
            current_user: User = Depends(require_pro_feature("has_themes"))
        ):
            ...

    Args:
        feature: Feature name to check

    Returns:
        Dependency function that raises HTTPException if feature is not available
    """

    def _check_feature(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session),
    ) -> User:
        if not is_plan_active(current_user) or not can_use_feature(
            current_user, feature
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a Pro subscription. Please upgrade to access {feature}.",
            )
        return current_user

    return _check_feature


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to require admin privileges.

    Usage:
        @router.get("/admin/endpoint")
        def admin_endpoint(
            current_user: User = Depends(require_admin)
        ):
            ...

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires administrator privileges.",
        )
    return current_user
