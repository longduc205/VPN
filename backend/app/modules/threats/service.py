from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.vpn_session import VpnSession


def serialize_event(event: SecurityEvent) -> dict:
    """Serializes a security event."""
    return {
        "id": event.id,
        "event_type": event.event_type,
        "severity": event.severity,
        "user_id": event.user_id,
        "source_ip": event.source_ip,
        "details": event.details,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def serialize_alert(alert: Alert) -> dict:
    """Serializes a security alert."""
    return {
        "id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "status": alert.status,
        "description": alert.description,
        "event_id": alert.event_id,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }


def create_security_event(
    db: Session,
    *,
    event_type: str,
    severity: str,
    title: str,
    description: str,
    user_id: Optional[str] = None,
    source_ip: Optional[str] = None,
    details: Optional[dict] = None,
) -> Alert:
    """Creates a security event and opens a corresponding system Alert."""
    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        source_ip=source_ip,
        details=details or {},
    )
    db.add(event)
    db.flush()
    
    alert = Alert(
        title=title,
        severity=severity,
        status="open",
        description=description,
        event_id=event.id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def open_alert_exists(db: Session, title: str) -> bool:
    """Checks if an active (unresolved) alert with the same title already exists."""
    return db.query(Alert).filter(Alert.title == title, Alert.status == "open").first() is not None


def inspect_failed_login(db: Session, *, username: str, source_ip: Optional[str]) -> Optional[Alert]:
    """Inspects recent failed logins to detect potential brute force attacks."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.brute_force_window_minutes)
    recent_logs = (
        db.query(AuditLog)
        .filter(AuditLog.action == "login_attempt", AuditLog.outcome == "failure", AuditLog.created_at >= cutoff)
        .all()
    )
    
    matches = [
        item
        for item in recent_logs
        if item.ip_address == source_ip or (isinstance(item.details, dict) and item.details.get("username") == username)
    ]
    
    if len(matches) < settings.brute_force_threshold:
        return None
        
    title = f"Possible brute-force login against {username}"
    if open_alert_exists(db, title):
        return None
        
    user = db.query(User).filter(User.username == username).first()
    return create_security_event(
        db,
        event_type="brute_force_login",
        severity="high",
        title=title,
        description=f"{len(matches)} failed login attempts detected within {settings.brute_force_window_minutes} minutes.",
        user_id=user.id if user else None,
        source_ip=source_ip,
        details={"username": username, "attempt_count": len(matches)},
    )


def detect_revoked_access(db: Session, *, user: User, source_ip: Optional[str]) -> Optional[Alert]:
    """Inspects and flags unauthorized config access from suspended/revoked users."""
    title = f"Revoked user attempted VPN access: {user.username}"
    if open_alert_exists(db, title):
        return None
    return create_security_event(
        db,
        event_type="revoked_user_access",
        severity="medium",
        title=title,
        description="A user with revoked or inactive VPN access attempted to retrieve a WireGuard config.",
        user_id=user.id,
        source_ip=source_ip,
        details={"username": user.username},
    )


def detect_traffic_spike(db: Session, *, session: VpnSession) -> Optional[Alert]:
    """Checks and triggers alerts if a session's traffic transfers exceed the threshold."""
    total = session.upload_bytes + session.download_bytes
    if total < settings.traffic_spike_bytes:
        return None
    title = f"Traffic spike for VPN session {session.id}"
    if open_alert_exists(db, title):
        return None
    return create_security_event(
        db,
        event_type="traffic_spike",
        severity="medium",
        title=title,
        description=f"Session transferred {total} bytes, exceeding the security threshold.",
        user_id=session.user_id,
        source_ip=session.source_ip,
        details={"session_id": session.id, "upload_bytes": session.upload_bytes, "download_bytes": session.download_bytes},
    )
