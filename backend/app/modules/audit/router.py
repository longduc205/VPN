import csv
import io
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.audit.service import serialize_audit

router = APIRouter()


@router.get("")
def list_audit_logs(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    """Admin/Auditor endpoint to retrieve system audit logs."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [serialize_audit(log) for log in logs]


@router.get("/export")
def export_audit_logs(
    _: User = Depends(require_role(["admin", "auditor"])),
    db: Session = Depends(get_db),
    format: str = Query(default="json", pattern="^(json|csv)$"),
    limit: int = Query(default=500, ge=1, le=2000),
):
    """Admin/Auditor endpoint to export audit logs in JSON or CSV format."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    rows = [serialize_audit(log) for log in logs]
    
    if format == "json":
        return rows
        
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "actor_id", "action", "ip_address", "outcome", "details", "created_at"],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
        
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit-export.csv"'},
    )
