from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class VpnProfileCreate(BaseModel):
    endpoint: Optional[str] = Field(default=None, max_length=255)
    dns: Optional[str] = Field(default=None, max_length=80)
    allowed_ips: Optional[str] = Field(default=None, max_length=255)


class VpnProfileRead(BaseModel):
    id: str
    user_id: str
    username: Optional[str] = None
    assigned_ip: str
    endpoint: str
    dns: str
    allowed_ips: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
