"""Full audit trail for a refund decision: what was sent to the model, what it said,
and what the deterministic policy engine actually decided. This is what makes a
decision explainable after the fact, and it's where prompt-injection attempts get
recorded for review even when the deterministic override already neutralized them.
"""

import uuid

from sqlalchemy import ARRAY, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from api_customer_refund_system.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DecisionLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "decision_logs"

    refund_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refund_requests.id"), nullable=False, index=True
    )
    model_used: Mapped[str | None] = mapped_column(default=None)
    prompt_snapshot: Mapped[str | None] = mapped_column(Text, default=None)
    raw_model_output: Mapped[dict | None] = mapped_column(JSONB, default=None)
    final_decision: Mapped[str] = mapped_column(nullable=False)
    final_reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[int] = mapped_column(nullable=False)
    flags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    latency_ms: Mapped[int | None] = mapped_column(default=None)
