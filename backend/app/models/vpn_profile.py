import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class VPNProfile(Base):
    __tablename__ = "vpn_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_ip = Column(String(64), nullable=False)
    endpoint = Column(String(255), nullable=False)
    dns = Column(String(80), nullable=False)
    allowed_ips = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="vpn_profiles")
    key = relationship("VpnKey", back_populates="profile", cascade="all, delete-orphan", uselist=False)
