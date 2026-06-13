from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="user")  # "admin", "user", "auditor"
    is_active: bool = True
    is_mfa_enabled: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long.")
        return v


class UserUpdate(BaseModel):
    email: Optional[str] = Field(default=None)
    full_name: Optional[str] = Field(default=None, max_length=255)
    password: Optional[str] = Field(default=None, min_length=12, max_length=128)
    role: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 12:
            raise ValueError("Password must be at least 12 characters long.")
        return v


class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
