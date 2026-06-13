from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.models.vpn_session import VpnSession
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.threats.service import detect_traffic_spike, serialize_alert, serialize_event

router = APIRouter()


@router.get("/events")
def list_security_events(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Admin/Auditor endpoint to list security events."""
    events = db.query(SecurityEvent).order_by(SecurityEvent.created_at.desc()).limit(200).all()
    return [serialize_event(event) for event in events]


@router.get("/alerts")
def list_alerts(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Admin/Auditor endpoint to list security alerts."""
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(200).all()
    return [serialize_alert(alert) for alert in alerts]


@router.post("/evaluate")
def evaluate_threats(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """Checks all online sessions for traffic spike threats."""
    created = 0
    sessions = db.query(VpnSession).filter(VpnSession.status == "online").all()
    for session in sessions:
        if detect_traffic_spike(db, session=session):
            created += 1
    return {"alerts_created": created}


@router.patch("/alerts/{alert_id}/resolve", status_code=status.HTTP_200_OK)
def resolve_alert(
    alert_id: str,
    _: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to resolve a security alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
        
    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return serialize_alert(alert)
