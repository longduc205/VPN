import logging
from typing import Optional, Any
from fastapi import Request
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_audit(
    db: Session,
    action: str,
    request: Request,
    status: str,
    user_id: Optional[str] = None,
    details: Optional[Any] = None
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

        # Build details dict
        details_payload = {}
        if isinstance(details, dict):
            details_payload = details
        elif isinstance(details, str):
            details_payload = {"message": details}

        audit_entry = AuditLog(
            actor_id=user_id,
            action=action,
            ip_address=ip_address,
            outcome=status,
            details=details_payload
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Audit log insertion failed: {e}", exc_info=True)


def serialize_audit(log: AuditLog) -> dict:
    """Serializes an AuditLog instance into a dictionary."""
    return {
        "id": log.id,
        "actor_id": log.actor_id,
        "action": log.action,
        "ip_address": log.ip_address,
        "outcome": log.outcome,
        "details": log.details,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
