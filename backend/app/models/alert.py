import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(180), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default="open", nullable=False, index=True)  # "open", "resolved"
    description = Column(Text, nullable=False)
    event_id = Column(String(36), ForeignKey("security_events.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
