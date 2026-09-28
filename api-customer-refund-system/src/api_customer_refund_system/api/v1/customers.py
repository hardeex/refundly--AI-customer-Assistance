import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from api_customer_refund_system.api.deps import get_current_tenant_id, get_db
from api_customer_refund_system.models.customer import Customer
from api_customer_refund_system.models.order import Order
from api_customer_refund_system.schemas.customer import CustomerListItem, CustomerOrdersOut

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerListItem])
def list_customers(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> list[Customer]:
    return (
        db.query(Customer)
        .filter(Customer.tenant_id == tenant_id)
        .order_by(Customer.name)
        .all()
    )


@router.get("/{customer_id}/orders", response_model=CustomerOrdersOut)
def get_customer_orders(
    customer_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> CustomerOrdersOut:
    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id, Customer.tenant_id == tenant_id)
        .first()
    )
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    orders = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.customer_id == customer_id, Order.tenant_id == tenant_id)
        .order_by(Order.order_date.desc())
        .all()
    )

    return CustomerOrdersOut(customer=customer, orders=orders)
