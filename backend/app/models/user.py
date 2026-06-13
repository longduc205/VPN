import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # "admin", "user", "auditor"
    is_active = Column(Boolean, nullable=False, default=True)
    is_vpn_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    vpn_profiles = relationship("VPNProfile", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("VpnSession", back_populates="user", cascade="all, delete-orphan")
    mfa_factors = relationship("MfaFactor", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", foreign_keys="[AuditLog.actor_id]")

    @property
    def is_mfa_enabled(self) -> bool:
        return self.mfa_secret is not None
