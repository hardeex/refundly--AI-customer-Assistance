from fastapi import APIRouter

from api_customer_refund_system.api.v1 import (
    auth,
    customers,
    health,
    policies,
    refund_requests,
    webhooks,
)

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(refund_requests.router)
api_router.include_router(customers.router)
api_router.include_router(policies.router)
api_router.include_router(webhooks.router)
