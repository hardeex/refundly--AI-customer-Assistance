"""Login for staff/admin users of a tenant's support dashboard.

There is deliberately no self-service registration endpoint: admin accounts are
provisioned out of band (see seed/seed_data.py for the demo admin account),
the same way you wouldn't want a public "create yourself an admin account" route
on a real support tool.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api_customer_refund_system.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from api_customer_refund_system.db.session import get_db
from api_customer_refund_system.models.user import User
from api_customer_refund_system.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Hashed once at import time and checked against on a "user not found" path, so
# that path takes roughly the same time as a real failed-password check instead
# of returning early and leaking, via timing, whether an email is registered.
_DUMMY_PASSWORD_HASH = hash_password("not-a-real-password")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()

    password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    valid_password = verify_password(payload.password, password_hash)
    if user is None or not valid_password or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    token = create_access_token(subject=str(user.id), tenant_id=str(user.tenant_id))
    return TokenResponse(access_token=token)
