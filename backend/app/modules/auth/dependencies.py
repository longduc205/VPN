from typing import List
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.modules.auth.helpers import verify_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    FastAPI dependency to retrieve the currently authenticated user.
    Extracts the JWT from the secure HttpOnly cookie (__Host-session)
    with a fallback to the Authorization header (useful for API docs/testing).
    """
    token = request.cookies.get("__Host-session")
    if not token:
        token = request.cookies.get("session_token")

    # Fallback to Authorization Header if cookie not found
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    role: str = payload.get("role")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated."
        )

    # Double check that the role matches the token's claim
    if user.role != role:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session role mismatch. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(allowed_roles: List[str]):
    """
    Factory dependency to enforce role-based access control.
    Returns a dependency that raises 403 Forbidden if the user's role is not allowed.
    """
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user
    return dependency
