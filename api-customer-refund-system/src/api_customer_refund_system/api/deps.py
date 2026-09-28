"""Shared FastAPI dependencies: DB session, and the two ways a request can prove
it belongs to a tenant - a tenant API key (for programmatic/integration callers)
or a staff JWT (for the admin dashboard). Both resolve to the same tenant_id, so
route handlers don't need to know or care which one was used.
"""

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from api_customer_refund_system.core.security import decode_access_token, hash_api_key
from api_customer_refund_system.db.session import get_db
from api_customer_refund_system.models.api_key import ApiKey
from api_customer_refund_system.models.user import User

API_KEY_PREFIX = "rf_live_"


def get_current_tenant_id(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header"
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be 'Bearer <token>'",
        )

    if token.startswith(API_KEY_PREFIX):
        return _tenant_id_from_api_key(token, db)
    return _tenant_id_from_jwt(token, db)


def _tenant_id_from_api_key(raw_key: str, db: Session) -> uuid.UUID:
    key_hash = hash_api_key(raw_key)
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
        .first()
    )
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked API key"
        )
    return api_key.tenant_id


def _tenant_id_from_jwt(token: str, db: Session) -> uuid.UUID:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from exc

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )
    return user.tenant_id
