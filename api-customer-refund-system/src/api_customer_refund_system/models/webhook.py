"""An endpoint a tenant has registered to receive decision callbacks. Payloads are
signed with `secret` (HMAC-SHA256) so the receiver can verify the request actually
came from us - the same pattern Stripe and GitHub use for their webhooks.
"""

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api_customer_refund_system.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Webhook(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "webhooks"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(nullable=False)
    secret: Mapped[str] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(default=True)
