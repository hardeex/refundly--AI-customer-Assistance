"""Tests for how a request resolves to a tenant - the piece every other
endpoint trusts. Covers both credential types (API key, staff JWT) and the
main ways each can fail.
"""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from api_customer_refund_system.api.deps import get_current_tenant_id
from api_customer_refund_system.core.security import (
    create_access_token,
    generate_api_key,
    hash_password,
)
from api_customer_refund_system.models.api_key import ApiKey
from api_customer_refund_system.models.tenant import Tenant
from api_customer_refund_system.models.user import User


def _make_tenant(db) -> Tenant:
    tenant = Tenant(name="Auth Test Co")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def test_valid_api_key_resolves_to_its_tenant(db):
    tenant = _make_tenant(db)
    raw_key, key_hash = generate_api_key()
    db.add(ApiKey(tenant_id=tenant.id, key_hash=key_hash))
    db.commit()

    resolved = get_current_tenant_id(authorization=f"Bearer {raw_key}", db=db)

    assert resolved == tenant.id


def test_revoked_api_key_is_rejected(db):
    tenant = _make_tenant(db)
    raw_key, key_hash = generate_api_key()
    db.add(ApiKey(tenant_id=tenant.id, key_hash=key_hash, revoked_at=datetime.now(UTC)))
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant_id(authorization=f"Bearer {raw_key}", db=db)

    assert exc_info.value.status_code == 401


def test_unknown_api_key_is_rejected(db):
    _make_tenant(db)  # a real tenant exists, just not one owning this key

    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant_id(authorization="Bearer rf_live_not_a_real_key", db=db)

    assert exc_info.value.status_code == 401


def test_valid_staff_jwt_resolves_to_its_tenant(db):
    tenant = _make_tenant(db)
    user = User(
        tenant_id=tenant.id,
        email="staff@example.com",
        password_hash=hash_password("irrelevant-for-this-test"),
        full_name="Staff Member",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), tenant_id=str(tenant.id))

    resolved = get_current_tenant_id(authorization=f"Bearer {token}", db=db)

    assert resolved == tenant.id


def test_jwt_for_a_deactivated_user_is_rejected(db):
    tenant = _make_tenant(db)
    user = User(
        tenant_id=tenant.id,
        email="disabled@example.com",
        password_hash=hash_password("irrelevant-for-this-test"),
        full_name="Disabled Staff",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), tenant_id=str(tenant.id))

    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant_id(authorization=f"Bearer {token}", db=db)

    assert exc_info.value.status_code == 401


def test_malformed_authorization_header_is_rejected(db):
    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant_id(authorization="not-a-bearer-token", db=db)

    assert exc_info.value.status_code == 401


def test_missing_authorization_header_is_rejected(db):
    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant_id(authorization=None, db=db)

    assert exc_info.value.status_code == 401
