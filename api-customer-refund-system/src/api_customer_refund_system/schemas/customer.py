import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    description: str | None
    price: float
    quantity: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_date: date
    total_amount: float
    status: str
    is_final_sale: bool
    items: list[OrderItemOut] = []


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    signup_date: date | None
    risk_flag: bool


class CustomerOrdersOut(BaseModel):
    customer: CustomerOut
    orders: list[OrderOut]


class CustomerListItem(BaseModel):
    """Slim shape for the customer picker in the chat UI - no order history,
    which is fetched separately once a customer is selected."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
