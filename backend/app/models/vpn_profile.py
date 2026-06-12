import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class VPNProfile(Base):
    __tablename__ = "vpn_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    client_ip = Column(String(45), nullable=False)  # Supports IPv4/IPv6 addresses
    public_key = Column(String(100), nullable=False)
    preshared_key = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="active")  # "active", "revoked"
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="vpn_profiles")
