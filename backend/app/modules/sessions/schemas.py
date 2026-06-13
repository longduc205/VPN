from pydantic import BaseModel, Field


class MockSessionCreate(BaseModel):
    user_id: str
    source_ip: str = Field(default="203.0.113.10", max_length=64)
    device: str = Field(default="demo-laptop", max_length=120)
    upload_bytes: int = Field(default=12_000_000, ge=0)
    download_bytes: int = Field(default=45_000_000, ge=0)
    status: str = Field(default="online", pattern="^(online|offline)$")


class SessionStatusUpdate(BaseModel):
    status: str = Field(pattern="^(online|offline)$")
