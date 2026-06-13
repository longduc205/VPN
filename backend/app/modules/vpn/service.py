import hashlib
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.models.vpn_profile import VPNProfile
from app.models.vpn_key import VpnKey
from app.modules.vpn.wireguard import (
    demo_preshared_key,
    demo_private_key,
    demo_public_key,
    render_config,
)


def get_user_or_404(db: Session, user_id: str) -> User:
    """Retrieves a user or raises 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def serialize_profile(profile: VPNProfile) -> dict:
    """Serializes a VPN profile for REST responses."""
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "username": profile.user.username if profile.user else None,
        "email": profile.user.email if profile.user else None,
        "assigned_ip": profile.assigned_ip,
        "endpoint": profile.endpoint,
        "dns": profile.dns,
        "allowed_ips": profile.allowed_ips,
        "is_active": profile.is_active,
        "revoked_at": profile.revoked_at.isoformat() if profile.revoked_at else None,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "public_key": profile.key.public_key if profile.key else None,
    }


def get_profile_or_404(db: Session, profile_id: str) -> VPNProfile:
    """Retrieves a profile or raises 404."""
    profile = db.query(VPNProfile).filter(VPNProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VPN profile not found")
    return profile


def get_active_profile_for_user(db: Session, user_id: str) -> Optional[VPNProfile]:
    """Retrieves the active profile for a specific user."""
    return (
        db.query(VPNProfile)
        .filter(VPNProfile.user_id == user_id, VPNProfile.is_active.is_(True))
        .order_by(VPNProfile.created_at.desc())
        .first()
    )


def create_profile_for_user(
    db: Session,
    *,
    user_id: str,
    endpoint: Optional[str] = None,
    dns: Optional[str] = None,
    allowed_ips: Optional[str] = None,
) -> VPNProfile:
    """Creates a new active VPN profile and generates mock cryptographic keys."""
    user = get_user_or_404(db, user_id)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create VPN profile for inactive user."
        )
    if get_active_profile_for_user(db, user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active VPN profile."
        )

    # Deterministically derive unique IP last octet from hashed UUID
    user_hash = int(hashlib.md5(user.id.encode("utf-8")).hexdigest(), 16)
    ip_last_octet = (user_hash % 200) + 10
    assigned_ip = f"{settings.vpn_subnet_prefix}.{ip_last_octet}/32"

    private_key = demo_private_key()
    profile = VPNProfile(
        user_id=user.id,
        assigned_ip=assigned_ip,
        endpoint=endpoint or settings.wireguard_endpoint,
        dns=dns or settings.wireguard_dns,
        allowed_ips=allowed_ips or settings.wireguard_allowed_ips,
        is_active=True,
    )
    db.add(profile)
    db.flush()

    db_key = VpnKey(
        profile_id=profile.id,
        private_key=private_key,
        public_key=demo_public_key(private_key),
        preshared_key=demo_preshared_key(),
    )
    db.add(db_key)

    user.is_vpn_enabled = True
    db.add(user)
    db.commit()
    db.refresh(profile)
    return profile


def revoke_profile(db: Session, profile: VPNProfile) -> VPNProfile:
    """Deactivates a profile and disables user's VPN status."""
    profile.is_active = False
    profile.revoked_at = datetime.now(timezone.utc)
    if profile.user:
        profile.user.is_vpn_enabled = False
        db.add(profile.user)

    # Auto-terminate any active VPN sessions for this user
    from app.models.vpn_session import VpnSession
    active_sessions = (
        db.query(VpnSession)
        .filter(VpnSession.user_id == profile.user_id, VpnSession.status == "online")
        .all()
    )
    for session in active_sessions:
        session.status = "offline"
        session.ended_at = datetime.now(timezone.utc)
        db.add(session)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def config_text(profile: VPNProfile) -> str:
    """Renders the text config content for the WireGuard interface."""
    return render_config(profile, settings.wireguard_server_public_key)


def assert_profile_download_allowed(profile: VPNProfile, current_user: User) -> None:
    """Verifies that the downloader is either the owner user or an admin."""
    if current_user.role == "admin":
        return
    if profile.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another user's VPN config."
        )
