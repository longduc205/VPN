import logging
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_audit(
    db: Session,
    action: str,
    request: Request,
    status: str,
    user_id: Optional[str] = None,
    details: Optional[str] = None
) -> None:
    """
    Safely records an entry in the system audit logs.
    Fails closed internally on DB error, logging the traceback but not raising
    to prevent blocking critical operations (like logins).
    """
    try:
        # Resolve real client IP considering reverse proxy headers
        ip_address = request.client.host if request.client else None
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()

        user_agent = request.headers.get("user-agent")

        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            status=status,
            details=details[:1000] if details else None
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Audit log insertion failed: {e}", exc_info=True)
