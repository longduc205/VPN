from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.audit.service import log_audit
from app.schemas.user import UserCreate, UserUpdate
from app.modules.users.service import (
    create_user,
    get_user_or_404,
    serialize_user,
    update_user,
)

router = APIRouter()


class RoleAssign(BaseModel):
    role: str = Field(..., pattern="^(admin|user|auditor)$")


@router.get("")
def list_users(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Admin/Auditor endpoint to list all system users."""
    users = db.query(User).order_by(User.username.asc()).all()
    return [serialize_user(user) for user in users]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_vpn_user(
    payload: UserCreate,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to create a new user."""
    user = create_user(db, payload)
    
    log_audit(
        db,
        action="create_user",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"username": user.username, "role": user.role}
    )
    
    return serialize_user(user)


@router.get("/{user_id}")
def get_user(
    user_id: str,
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin/Auditor endpoint to fetch a single user."""
    return serialize_user(get_user_or_404(db, user_id))


@router.patch("/{user_id}")
def patch_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to update user fields."""
    user = update_user(db, get_user_or_404(db, user_id), payload)
    
    log_audit(
        db,
        action="update_user",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"target_user": user.username, "updated_fields": payload.model_dump(exclude_unset=True)}
    )
    
    return serialize_user(user)


@router.post("/{user_id}/disable")
def disable_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to deactivate a user and disable their VPN access."""
    user = get_user_or_404(db, user_id)
    user.is_active = False
    user.is_vpn_enabled = False
    db.commit()
    db.refresh(user)
    
    log_audit(
        db,
        action="disable_user",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"target_user": user.username}
    )
    
    return serialize_user(user)


@router.post("/{user_id}/enable")
def enable_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to activate a deactivated user."""
    user = get_user_or_404(db, user_id)
    user.is_active = True
    db.commit()
    db.refresh(user)
    
    log_audit(
        db,
        action="enable_user",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"target_user": user.username}
    )
    
    return serialize_user(user)


@router.patch("/{user_id}/role")
def assign_role(
    user_id: str,
    payload: RoleAssign,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to change a user's role."""
    user = get_user_or_404(db, user_id)
    user.role = payload.role
    db.commit()
    db.refresh(user)
    
    log_audit(
        db,
        action="assign_role",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"target_user": user.username, "role": payload.role}
    )
    
    return serialize_user(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> None:
    """Admin endpoint to delete a user from the system."""
    user = get_user_or_404(db, user_id)
    
    log_audit(
        db,
        action="delete_user",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"deleted_user": user.username}
    )
    
    db.delete(user)
    db.commit()
