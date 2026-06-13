from datetime import datetime, time, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.vpn_profile import VPNProfile
from app.models.vpn_session import VpnSession
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.audit.service import serialize_audit
from app.modules.sessions.service import serialize_session, update_active_session_metric
from app.modules.threats.service import serialize_alert

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_data(
    _: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> dict:
    """Admin endpoint to fetch consolidated operations metrics and recent entities."""
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)
    update_active_session_metric(db)
    
    recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    active_sessions = db.query(VpnSession).filter(VpnSession.status == "online").order_by(VpnSession.started_at.desc()).limit(10).all()
    alerts = db.query(Alert).filter(Alert.status == "open").order_by(Alert.created_at.desc()).limit(10).all()
    
    failed_logins = db.query(AuditLog).filter(
        AuditLog.action == "login_attempt",
        AuditLog.outcome == "failure",
        AuditLog.created_at >= today_start
    ).count()

    return {
        "stats": {
            "total_users": db.query(User).count(),
            "active_vpn_users": db.query(User).filter(User.is_vpn_enabled.is_(True)).count(),
            "active_sessions": db.query(VpnSession).filter(VpnSession.status == "online").count(),
            "failed_logins_today": failed_logins,
            "alerts": db.query(Alert).filter(Alert.status == "open").count(),
            "vpn_profiles": db.query(VPNProfile).count(),
        },
        "recent_audit_logs": [serialize_audit(log) for log in recent_logs],
        "active_sessions": [serialize_session(session) for session in active_sessions],
        "security_alerts": [serialize_alert(alert) for alert in alerts],
    }
