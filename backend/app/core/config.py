import os
import secrets
import logging
from pydantic import BaseModel

# Try to load .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


class Settings(BaseModel):
    app_name: str = "VPN Management System"
    environment: str = os.getenv("ENVIRONMENT", "development")
    api_prefix: str = "/api"
    
    database_url: str = os.getenv("DATABASE_URL", "postgresql://vpn:vpn@localhost:5432/vpn")
    jwt_secret: str = ""
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # WireGuard configurations
    wireguard_endpoint: str = os.getenv("WIREGUARD_ENDPOINT", "vpn.example.local:51820")
    wireguard_server_public_key: str = os.getenv("WIREGUARD_SERVER_PUBLIC_KEY", "hElLoWgSeRvErPuBlIcKeYdEmO1234567890abcdefg=")
    wireguard_dns: str = os.getenv("WIREGUARD_DNS", "1.1.1.1")
    wireguard_allowed_ips: str = os.getenv("WIREGUARD_ALLOWED_IPS", "0.0.0.0/0, ::/0")
    vpn_subnet_prefix: str = os.getenv("VPN_SUBNET_PREFIX", "10.8.0")

    # Threat detection parameters
    brute_force_threshold: int = int(os.getenv("BRUTE_FORCE_THRESHOLD", "5"))
    brute_force_window_minutes: int = int(os.getenv("BRUTE_FORCE_WINDOW_MINUTES", "15"))
    traffic_spike_bytes: int = int(os.getenv("TRAFFIC_SPIKE_BYTES", str(5 * 1024 * 1024 * 1024)))

    def __init__(self, **data):
        super().__init__(**data)
        secret = os.getenv("JWT_SECRET")
        if not secret or secret == "change-me":
            if self.environment == "production":
                raise ValueError("JWT_SECRET must be set to a secure value in production!")
            
            # Development fallback: query file or generate ephemeral
            jwt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "jwt_secret.txt")
            if os.path.exists(jwt_file):
                try:
                    with open(jwt_file, "r") as f:
                        self.jwt_secret = f.read().strip()
                except Exception:
                    pass
            
            if not self.jwt_secret:
                self.jwt_secret = secrets.token_hex(32)
                try:
                    with open(jwt_file, "w") as f:
                        f.write(self.jwt_secret)
                except Exception:
                    pass
                logging.warning("Generating ephemeral JWT_SECRET for development. Instance-isolated!")
        else:
            self.jwt_secret = secret


settings = Settings()
