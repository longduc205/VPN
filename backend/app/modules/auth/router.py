import time
from collections import defaultdict
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import UserLogin
from app.modules.auth.helpers import verify_password, get_password_hash, create_access_token
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.audit.service import log_audit

router = APIRouter()

# In-memory IP-based rate limiting dictionary
LOGIN_ATTEMPTS = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
MAX_ATTEMPTS_PER_MINUTE = 5


def is_rate_limited(ip: str) -> bool:
    """Checks if the client IP has exceeded the max login attempts limit."""
    now = time.time()
    # Prune attempts older than the window
    LOGIN_ATTEMPTS[ip] = [t for t in LOGIN_ATTEMPTS[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(LOGIN_ATTEMPTS[ip]) >= MAX_ATTEMPTS_PER_MINUTE:
        return True
    LOGIN_ATTEMPTS[ip].append(now)
    return False


@router.post("/login")
def login(
    request: Request,
    response: Response,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    # Retrieve client IP for audit logs & rate limiting
    ip = request.client.host if request.client else "unknown"
    
    # 1. Enforce Rate Limiting
    if is_rate_limited(ip):
        log_audit(
            db,
            action="login_rate_limit_exceeded",
            request=request,
            status="failure",
            details=f"Rate limit exceeded for IP: {ip}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in 1 minute."
        )

    # 2. Query User
    user = db.query(User).filter(User.username == credentials.username).first()
    
    # 3. Verify Credentials (fail with generic error message to prevent username enumeration)
    if not user or not verify_password(credentials.password, user.hashed_password):
        log_audit(
            db,
            action="login_attempt",
            request=request,
            status="failure",
            user_id=user.id if user else None,
            details=f"Failed login attempt for username: {credentials.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password."
        )

    if not user.is_active:
        log_audit(
            db,
            action="login_attempt",
            request=request,
            status="failure",
            user_id=user.id,
            details="Login blocked: User account deactivated"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated."
        )

    # 4. Generate Token
    token_data = {"sub": user.id, "role": user.role}
    access_token = create_access_token(token_data)

    # Determine secure cookie settings (Fallback to session_token in HTTP dev environment)
    is_https = request.url.scheme == "https" or settings.environment == "production"
    cookie_name = "__Host-session" if is_https else "session_token"
    secure_flag = True if cookie_name.startswith("__Host-") else False

    # 5. Set HttpOnly Cookie
    response.set_cookie(
        key=cookie_name,
        value=access_token,
        httponly=True,
        secure=secure_flag,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )

    log_audit(
        db,
        action="login_attempt",
        request=request,
        status="success",
        user_id=user.id,
        details="User logged in successfully"
    )

    return {"message": "Logged in successfully", "role": user.role, "username": user.username}


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Determine the cookie name dynamically
    is_https = request.url.scheme == "https" or settings.environment == "production"
    cookie_name = "__Host-session" if is_https else "session_token"
    
    # Delete the cookie by setting max_age=0
    response.delete_cookie(
        key=cookie_name,
        path="/"
    )
    
    log_audit(
        db,
        action="logout",
        request=request,
        status="success",
        user_id=current_user.id,
        details="User logged out"
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns details of the currently authenticated session user."""
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    request: Request,
    new_user: UserCreate,
    admin_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Admin-only endpoint to register/create new system users.
    Enforces password strength validation and logs the admin action.
    """
    # Check duplicate username
    existing_user = db.query(User).filter(User.username == new_user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken."
        )

    # Hash the password
    hashed_pwd = get_password_hash(new_user.password)

    db_user = User(
        username=new_user.username,
        hashed_password=hashed_pwd,
        role=new_user.role,
        is_active=new_user.is_active
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        log_audit(
            db,
            action="user_create",
            request=request,
            status="success",
            user_id=admin_user.id,
            details=f"Admin created user: {db_user.username} (role: {db_user.role})"
        )

        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to database error."
        )
