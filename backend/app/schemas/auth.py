from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    sub: str  # user_id
    role: str
    exp: int


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=12, max_length=128)
