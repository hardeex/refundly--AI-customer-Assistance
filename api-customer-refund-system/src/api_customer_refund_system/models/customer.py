"""Mock CRM record: one of a tenant's end customers."""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api_customer_refund_system.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from api_customer_refund_system.models.order import Order


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    signup_date: Mapped[date | None] = mapped_column(Date, default=None)
    # Flagged when a customer has a history of disputed or abusive refund claims.
    # The AI layer reads this as context; it never decides on it alone (see policy_engine).
    risk_flag: Mapped[bool] = mapped_column(default=False)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
