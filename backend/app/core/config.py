from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "VPN Management System"
    environment: str = "development"
    api_prefix: str = "/api"


settings = Settings()
