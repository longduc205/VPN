import time
from collections import defaultdict
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import UserLogin, MfaVerifyRequest, MfaLoginRequest
from app.models.mfa_factor import MfaFactor
from app.modules.auth.helpers import verify_password, get_password_hash, create_access_token
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.audit.service import log_audit
from app.modules.threats.service import inspect_failed_login
from app.modules.auth.mfa import generate_mfa_secret, verify_totp_token, get_provisioning_uri

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
            details={"username": credentials.username}
        )
        inspect_failed_login(db, username=credentials.username, source_ip=ip)
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
            details={"username": credentials.username, "reason": "deactivated"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated."
        )

    # Check if user has MFA active
    mfa_active = False
    if user.mfa_secret:
        mfa_factor = db.query(MfaFactor).filter(MfaFactor.user_id == user.id, MfaFactor.is_enabled == True).first()
        if mfa_factor:
            mfa_active = True

    if mfa_active:
        log_audit(
            db,
            action="login_mfa_required",
            request=request,
            status="success",
            user_id=user.id,
            details={"username": user.username, "message": "Password verified, MFA code required"}
        )
        return {"status": "mfa_required", "username": user.username}

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


@router.post("/login/mfa")
def login_mfa(
    request: Request,
    response: Response,
    payload: MfaLoginRequest,
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else "unknown"

    # Enforce Rate Limiting
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

    # 1. Query User
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active or not user.mfa_secret:
        log_audit(
            db,
            action="login_mfa_attempt",
            request=request,
            status="failure",
            details={"username": payload.username, "reason": "user_invalid_or_no_mfa"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authentication code."
        )

    # 2. Verify OTP code
    if not verify_totp_token(user.mfa_secret, payload.code):
        log_audit(
            db,
            action="login_mfa_attempt",
            request=request,
            status="failure",
            user_id=user.id,
            details={"username": payload.username, "reason": "otp_invalid"}
        )
        inspect_failed_login(db, username=payload.username, source_ip=ip)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authentication code."
        )

    # 3. Generate Token
    token_data = {"sub": user.id, "role": user.role}
    access_token = create_access_token(token_data)

    is_https = request.url.scheme == "https" or settings.environment == "production"
    cookie_name = "__Host-session" if is_https else "session_token"
    secure_flag = True if cookie_name.startswith("__Host-") else False

    # 4. Set HttpOnly Cookie
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
        action="login_mfa_attempt",
        request=request,
        status="success",
        user_id=user.id,
        details="User logged in successfully via 2FA"
    )

    return {"message": "Logged in successfully", "role": user.role, "username": user.username}


@router.post("/mfa/enroll")
def mfa_enroll(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates a new MFA base32 secret and provisioning URL."""
    active_factor = db.query(MfaFactor).filter(MfaFactor.user_id == current_user.id, MfaFactor.is_enabled == True).first()
    if active_factor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled on this account."
        )

    secret = generate_mfa_secret()
    provisioning_uri = get_provisioning_uri(current_user.username, secret)

    current_user.mfa_secret = secret
    db.add(current_user)
    db.commit()

    log_audit(
        db,
        action="mfa_enroll_start",
        request=request,
        status="success",
        user_id=current_user.id,
        details="MFA enrollment initiated"
    )

    return {"secret": secret, "provisioning_uri": provisioning_uri}


@router.post("/mfa/verify")
def mfa_verify(
    request: Request,
    payload: MfaVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifies the first TOTP token to activate 2FA."""
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA enrollment has not been initiated."
        )

    if not verify_totp_token(current_user.mfa_secret, payload.code):
        log_audit(
            db,
            action="mfa_verify",
            request=request,
            status="failure",
            user_id=current_user.id,
            details="Invalid OTP verification code"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code."
        )

    mfa_factor = db.query(MfaFactor).filter(MfaFactor.user_id == current_user.id).first()
    if not mfa_factor:
        mfa_factor = MfaFactor(
            user_id=current_user.id,
            factor_type="totp",
            label="Google Authenticator",
            is_enabled=True
        )
        db.add(mfa_factor)
    else:
        mfa_factor.is_enabled = True
        db.add(mfa_factor)

    db.commit()

    log_audit(
        db,
        action="mfa_verify",
        request=request,
        status="success",
        user_id=current_user.id,
        details="MFA successfully activated"
    )

    return {"message": "MFA activated successfully"}


@router.post("/mfa/disable")
def mfa_disable(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disables MFA for the current user."""
    current_user.mfa_secret = None
    db.add(current_user)

    mfa_factors = db.query(MfaFactor).filter(MfaFactor.user_id == current_user.id).all()
    for factor in mfa_factors:
        factor.is_enabled = False
        db.add(factor)

    db.commit()

    log_audit(
        db,
        action="mfa_disable",
        request=request,
        status="success",
        user_id=current_user.id,
        details="MFA deactivated by user"
    )

    return {"message": "MFA disabled successfully"}
