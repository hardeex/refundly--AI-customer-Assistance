"""A tenant is a connected business (e-commerce store, helpdesk, etc.) using Refundly."""

from sqlalchemy.orm import Mapped, mapped_column

from api_customer_refund_system.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(nullable=False)
