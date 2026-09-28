"""A tenant's refund policy, stored two ways at once:

- `rules_json` holds the handful of hard thresholds the policy engine checks
  deterministically (see services.policy_engine) - amounts, day windows, that kind
  of thing. Never trust the AI to enforce these; it just isn't reliable at treating
  a number as a hard boundary the way a plain `if` statement is.
- `policy_text` is the prose version, which is what actually goes in the AI's
  system prompt. It carries nuance the JSON can't express, e.g. the difference
  between "arrived damaged" and "customer changed their mind."

Both are versioned together so any historical decision can be traced back to the
exact policy that produced it.
"""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from api_customer_refund_system.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefundPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refund_policies"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(nullable=False)
    rules_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    policy_text: Mapped[str] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(default=True)
