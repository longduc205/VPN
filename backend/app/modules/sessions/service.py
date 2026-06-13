from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.metrics import ACTIVE_SESSIONS_GAUGE
from app.models.user import User
from app.models.vpn_session import VpnSession
from app.modules.sessions.schemas import MockSessionCreate


def serialize_session(session: VpnSession) -> dict:
    """Serializes a VPN session entity for API responses."""
    return {
        "id": session.id,
        "user_id": session.user_id,
        "username": session.user.username if session.user else None,
        "source_ip": session.source_ip,
        "device": session.device,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "upload_bytes": session.upload_bytes,
        "download_bytes": session.download_bytes,
        "status": session.status,
    }


def get_user_or_404(db: Session, user_id: str) -> User:
    """Helper method to retrieve user or raise 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def update_active_session_metric(db: Session) -> None:
    """Helper to update current active sessions metrics."""
    count = db.query(VpnSession).filter(VpnSession.status == "online").count()
    ACTIVE_SESSIONS_GAUGE.labels().inc() # Sets placeholder dummy


def create_mock_session(db: Session, payload: MockSessionCreate) -> VpnSession:
    """Admin endpoint service to mock connection sessions."""
    user = get_user_or_404(db, payload.user_id)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create session for inactive user"
        )
    session = VpnSession(
        user_id=user.id,
        source_ip=payload.source_ip,
        device=payload.device,
        upload_bytes=payload.upload_bytes,
        download_bytes=payload.download_bytes,
        status=payload.status,
        ended_at=None if payload.status == "online" else datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    update_active_session_metric(db)
    return session


def set_session_status(db: Session, session: VpnSession, status_value: str) -> VpnSession:
    """Updates session status online/offline and timestamps end time."""
    session.status = status_value
    session.ended_at = None if status_value == "online" else datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(session)
    update_active_session_metric(db)
    return session


def get_session_or_404(db: Session, session_id: str) -> VpnSession:
    """Retrieves session or raises 404."""
    session = db.query(VpnSession).filter(VpnSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VPN session not found")
    return session
