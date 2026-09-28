"""Import every model so they register on Base.metadata - Alembic's autogenerate
and Base.metadata.create_all() both rely on that registration having happened.
"""

from api_customer_refund_system.models.api_key import ApiKey
from api_customer_refund_system.models.customer import Customer
from api_customer_refund_system.models.decision_log import DecisionLog
from api_customer_refund_system.models.order import Order, OrderItem
from api_customer_refund_system.models.policy import RefundPolicy
from api_customer_refund_system.models.refund_request import RefundRequest
from api_customer_refund_system.models.tenant import Tenant
from api_customer_refund_system.models.user import User
from api_customer_refund_system.models.webhook import Webhook

__all__ = [
    "ApiKey",
    "Customer",
    "DecisionLog",
    "Order",
    "OrderItem",
    "RefundPolicy",
    "RefundRequest",
    "Tenant",
    "User",
    "Webhook",
]
