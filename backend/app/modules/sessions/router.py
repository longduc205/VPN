from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.vpn_session import VpnSession
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.audit.service import log_audit
from app.modules.sessions.schemas import MockSessionCreate, SessionStatusUpdate
from app.modules.sessions.service import (
    create_mock_session,
    get_session_or_404,
    serialize_session,
    set_session_status,
)
from app.modules.threats.service import detect_traffic_spike

router = APIRouter()


@router.get("")
def list_sessions(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Admin/Auditor endpoint to view all session histories."""
    sessions = db.query(VpnSession).order_by(VpnSession.started_at.desc()).limit(200).all()
    return [serialize_session(session) for session in sessions]


@router.get("/me")
def my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Logged-in user endpoint to view their own sessions."""
    sessions = (
        db.query(VpnSession)
        .filter(VpnSession.user_id == current_user.id)
        .order_by(VpnSession.started_at.desc())
        .limit(100)
        .all()
    )
    return [serialize_session(session) for session in sessions]


@router.post("/mock")
def add_mock_session(
    payload: MockSessionCreate,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to create a mock session and evaluate traffic threats."""
    session = create_mock_session(db, payload)
    detect_traffic_spike(db, session=session)
    
    log_audit(
        db,
        action="create_mock_session",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"user_id": payload.user_id, "session_id": session.id, "status": payload.status}
    )
    
    return serialize_session(session)


@router.patch("/{session_id}/status")
def update_session_status(
    session_id: str,
    payload: SessionStatusUpdate,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to update mock session status (online/offline)."""
    session = set_session_status(db, get_session_or_404(db, session_id), payload.status)
    
    log_audit(
        db,
        action="update_session_status",
        request=request,
        status="success",
        user_id=current_user.id,
        details={"session_id": session.id, "status": payload.status}
    )
    
    return serialize_session(session)
