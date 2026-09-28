"""Create a new version of a tenant's refund policy. Policies are append-only and
versioned rather than edited in place, so a decision made under an old policy can
always be traced back to the exact rules that produced it (see decision_logs).
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api_customer_refund_system.api.deps import get_current_tenant_id, get_db
from api_customer_refund_system.models.policy import RefundPolicy
from api_customer_refund_system.schemas.policy import PolicyCreate, PolicyOut

router = APIRouter(prefix="/policies", tags=["policies"])


@router.post("", response_model=PolicyOut, status_code=status.HTTP_201_CREATED)
def create_policy(
    payload: PolicyCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> PolicyOut:
    current = (
        db.query(RefundPolicy)
        .filter(RefundPolicy.tenant_id == tenant_id)
        .order_by(RefundPolicy.version.desc())
        .first()
    )
    next_version = (current.version + 1) if current else 1

    # Deactivate the previous version so exactly one policy is ever active per
    # tenant - the query in refund_requests.py relies on that invariant.
    if current is not None and current.active:
        current.active = False

    new_policy = RefundPolicy(
        tenant_id=tenant_id,
        version=next_version,
        rules_json=payload.rules_json,
        policy_text=payload.policy_text,
        active=True,
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return new_policy
