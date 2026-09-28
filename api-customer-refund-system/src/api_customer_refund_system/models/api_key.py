"""Credentials a tenant's own systems (their cart, helpdesk, CRM) use to call the API.

The raw key is only ever shown once, at creation time. We store a SHA-256 hash and
look up incoming requests by that hash - see core.security.hash_api_key for why
SHA-256 rather than bcrypt is the right choice here.
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api_customer_refund_system.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ApiKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_keys"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    label: Mapped[str | None] = mapped_column(default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)
