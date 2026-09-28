import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RefundRequestCreate(BaseModel):
    customer_id: uuid.UUID
    order_id: uuid.UUID
    message: str = Field(min_length=1, max_length=4000)
    requested_amount: float | None = Field(default=None, ge=0)


class RefundRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    reasoning: str
    policy_version: int
    flags: list[str]
    created_at: datetime


class RefundRequestListItem(BaseModel):
    """Row shape for the admin dashboard's request list - includes enough context
    (customer, message, amounts) that a support agent doesn't have to open every request."""

    id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str
    order_id: uuid.UUID
    message: str
    requested_amount: float | None
    status: str
    reasoning: str | None
    flags: list[str]
    created_at: datetime
    resolved_at: datetime | None
