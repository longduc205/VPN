import base64
import hashlib
import hmac
import secrets
import struct
import time
import urllib.parse


def generate_mfa_secret() -> str:
    """Generates a random 32-character base32 secret key (160 bits seed)."""
    random_bytes = secrets.token_bytes(20)
    return base64.b32encode(random_bytes).decode("utf-8").replace("=", "")


def get_hotp_token(secret: str, intervals_no: int) -> str:
    """Calculates a standard 6-digit HOTP token for a base32 secret and interval number."""
    try:
        # Pad secret if length is not multiple of 8
        padding = (8 - len(secret) % 8) % 8
        secret_padded = secret + "=" * padding
        key = base64.b32decode(secret_padded.encode("utf-8"), casefold=True)
    except Exception as e:
        raise ValueError(f"Invalid base32 secret: {e}")

    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    token = (struct.unpack(">I", h[o : o + 4])[0] & 0x7FFFFFFF) % 1000000
    return f"{token:06d}"


def verify_totp_token(secret: str, token: str, window: int = 1) -> bool:
    """
    Verifies a 6-digit TOTP token against a base32 secret.
    Allows for time drift window (defaults to 1 step before/after = 30 seconds drift).
    """
    if not secret or not token or len(token) != 6 or not token.isdigit():
        return False

    current_time_step = int(time.time() / 30)

    # Check current time step and adjacent windows
    for i in range(-window, window + 1):
        if get_hotp_token(secret, current_time_step + i) == token:
            return True

    return False


def get_provisioning_uri(username: str, secret: str, issuer: str = "AEGIS VPN") -> str:
    """Generates the standard otpauth provisioning URL for Authenticator apps."""
    issuer_quoted = urllib.parse.quote(issuer)
    user_quoted = urllib.parse.quote(username)
    return f"otpauth://totp/{issuer_quoted}:{user_quoted}?secret={secret}&issuer={issuer_quoted}"
