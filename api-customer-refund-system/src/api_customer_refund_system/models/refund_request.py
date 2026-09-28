"""One row per customer refund request. `message` is the customer's raw text and is
treated as untrusted input throughout the AI layer - see services.ai.prompts.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api_customer_refund_system.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"


class RefundRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refund_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'denied', 'escalated')",
            name="ck_refund_requests_status",
        ),
        # Lets a client safely retry a POST after a dropped connection without
        # risking a duplicate refund request being created.
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_refund_requests_idempotency"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default=RefundStatus.PENDING.value)
    requested_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), default=None)
    idempotency_key: Mapped[str | None] = mapped_column(default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)
