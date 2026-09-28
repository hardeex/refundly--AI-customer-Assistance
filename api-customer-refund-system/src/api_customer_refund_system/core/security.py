"""Password hashing and JWT helpers for the admin/support dashboard login."""

import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import bcrypt
from jose import JWTError, jwt

from api_customer_refund_system.core.config import get_settings

settings = get_settings()

# bcrypt's own algorithm caps input at 72 bytes; anything past that is silently
# ignored rather than hashed, so a long password would collide with any other
# password sharing the same first 72 bytes. Reject it up front instead.
_MAX_PASSWORD_BYTES = 72


def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > _MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {_MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


def create_access_token(subject: str, tenant_id: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "tenant_id": tenant_id, "exp": expires_at, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload


def generate_api_key() -> tuple[str, str]:
    """Return (raw_key, key_hash). The raw key is shown to the caller once and never stored."""
    raw_key = f"rf_live_{secrets.token_urlsafe(32)}"
    return raw_key, hash_api_key(raw_key)


def hash_api_key(raw_key: str) -> str:
    """API keys are hashed with SHA-256, not bcrypt: they're already high-entropy random
    tokens (unlike user passwords), so we don't need bcrypt's deliberate slowness - and a
    fast, deterministic hash lets us look the key up by an indexed column instead of
    checking it against every stored hash on every request."""
    return sha256(raw_key.encode("utf-8")).hexdigest()
