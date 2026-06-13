from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.metrics import GENERATED_CONFIGS_COUNT
from app.models.user import User
from app.models.vpn_profile import VPNProfile
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.audit.service import log_audit
from app.modules.threats.service import detect_revoked_access
from app.modules.vpn.schemas import VpnProfileCreate
from app.modules.vpn.service import (
    assert_profile_download_allowed,
    config_text,
    create_profile_for_user,
    get_active_profile_for_user,
    get_profile_or_404,
    revoke_profile,
    serialize_profile,
)

router = APIRouter()


@router.get("/profiles")
def list_profiles(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Admin/Auditor endpoint to list all VPN profiles."""
    profiles = db.query(VPNProfile).order_by(VPNProfile.created_at.desc()).all()
    return [serialize_profile(profile) for profile in profiles]


@router.post("/users/{user_id}/profile", status_code=status.HTTP_201_CREATED)
def create_user_profile(
    user_id: str,
    payload: VpnProfileCreate,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to provision a new WireGuard configuration for a user."""
    profile = create_profile_for_user(
        db,
        user_id=user_id,
        endpoint=payload.endpoint,
        dns=payload.dns,
        allowed_ips=payload.allowed_ips,
    )
    
    log_audit(
        db,
        action="create_vpn_profile",
        request=request,
        status="success",
        user_id=current_user.id,
        details=f"Admin created profile {profile.id} for user {user_id} with IP {profile.assigned_ip}"
    )
    
    return serialize_profile(profile)


@router.get("/my-profile")
def my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Logged-in user endpoint to fetch their own active VPN profile."""
    profile = get_active_profile_for_user(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active VPN profile found.")
    return serialize_profile(profile)


@router.get("/my-profile/config")
def download_my_config(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    """Logged-in user endpoint to download their own WireGuard configuration."""
    profile = get_active_profile_for_user(db, current_user.id)
    ip = request.client.host if request.client else "unknown"

    if not profile or not current_user.is_vpn_enabled:
        detect_revoked_access(db, user=current_user, source_ip=ip)
        log_audit(
            db,
            action="generate_vpn_config",
            request=request,
            status="failure",
            user_id=current_user.id,
            details="Profile missing or user VPN access has been revoked"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="VPN access is not active.")
    
    GENERATED_CONFIGS_COUNT.inc()
    
    log_audit(
        db,
        action="generate_vpn_config",
        request=request,
        status="success",
        user_id=current_user.id,
        details=f"Generated config file for profile {profile.id}"
    )
    
    return PlainTextResponse(
        config_text(profile),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{current_user.username}-wireguard.conf"'},
    )


@router.get("/profiles/{profile_id}/config")
def download_profile_config(
    profile_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    """Download specific configuration file (Admin or Owner user)."""
    profile = get_profile_or_404(db, profile_id)
    assert_profile_download_allowed(profile, current_user)
    ip = request.client.host if request.client else "unknown"

    if not profile.is_active:
        detect_revoked_access(db, user=profile.user, source_ip=ip)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="VPN profile is revoked.")
    
    GENERATED_CONFIGS_COUNT.inc()
    
    log_audit(
        db,
        action="generate_vpn_config",
        request=request,
        status="success",
        user_id=current_user.id,
        details=f"Downloaded config file for profile {profile.id}"
    )
    
    return PlainTextResponse(
        config_text(profile),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="profile-{profile.id}-wireguard.conf"'},
    )


@router.post("/profiles/{profile_id}/revoke")
def revoke_user_profile(
    profile_id: str,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to revoke a VPN profile."""
    profile = revoke_profile(db, get_profile_or_404(db, profile_id))
    
    log_audit(
        db,
        action="revoke_vpn_access",
        request=request,
        status="success",
        user_id=current_user.id,
        details=f"Admin revoked profile {profile.id} for user {profile.user_id}"
    )
    
    return serialize_profile(profile)
