from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    sub: str  # user_id
    role: str
    exp: int


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class MfaVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d+$")


class MfaLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d+$")
