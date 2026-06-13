import uuid
from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class VpnSession(Base):
    __tablename__ = "vpn_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_ip = Column(String(64), nullable=False)
    device = Column(String(120), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    upload_bytes = Column(BigInteger, default=0, nullable=False)
    download_bytes = Column(BigInteger, default=0, nullable=False)
    status = Column(String(20), default="online", nullable=False)  # "online", "offline"

    user = relationship("User", back_populates="sessions")
