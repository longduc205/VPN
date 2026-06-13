from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.user import User
from app.modules.auth.helpers import get_password_hash
from app.schemas.user import UserCreate, UserUpdate


def serialize_user(user: User) -> dict:
    """Serializes a User entity for REST responses."""
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_vpn_enabled": user.is_vpn_enabled,
        "is_mfa_enabled": user.is_mfa_enabled,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def get_user_or_404(db: Session, user_id: str) -> User:
    """Retrieves a user by UUID or raises 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def create_user(db: Session, payload: UserCreate) -> User:
    """Creates a new system user with password hashing."""
    duplicate = (
        db.query(User)
        .filter(or_(User.email == payload.email, User.username == payload.username))
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists.")

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name or payload.username,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """Updates selected user columns."""
    data = payload.model_dump(exclude_unset=True)
    
    password = data.pop("password", None)
    if password:
        user.hashed_password = get_password_hash(password)

    for field, value in data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
