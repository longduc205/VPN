import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class VpnKey(Base):
    __tablename__ = "vpn_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("vpn_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    private_key = Column(String(128), nullable=False)
    public_key = Column(String(128), nullable=False)
    preshared_key = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    profile = relationship("VPNProfile", back_populates="key")
