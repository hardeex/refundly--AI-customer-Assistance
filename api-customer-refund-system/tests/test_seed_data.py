"""Regression coverage for the seed script's --reset path.

A prior version deleted orders/customers before the refund_requests and
decision_logs that reference them, which Postgres correctly rejected with a
foreign key violation the moment any request had actually been submitted
through the API (exactly what happens during normal local testing). This
pins the fix: reseeding after real usage must still work.
"""

from api_customer_refund_system.models.customer import Customer
from api_customer_refund_system.models.decision_log import DecisionLog
from api_customer_refund_system.models.order import Order
from api_customer_refund_system.models.refund_request import RefundRequest
from api_customer_refund_system.models.tenant import Tenant
from api_customer_refund_system.seed.seed_data import CUSTOMERS, seed


def test_reset_succeeds_after_a_refund_request_has_been_submitted(db):
    seed(db, reset=False)

    tenant = db.query(Tenant).filter(Tenant.name == "Northwind Outfitters").one()
    customer = db.query(Customer).filter(Customer.tenant_id == tenant.id).first()
    order = db.query(Order).filter(Order.customer_id == customer.id).first()

    refund_request = RefundRequest(
        tenant_id=tenant.id,
        customer_id=customer.id,
        order_id=order.id,
        message="test message",
        status="approved",
    )
    db.add(refund_request)
    db.flush()
    db.add(
        DecisionLog(
            refund_request_id=refund_request.id,
            final_decision="approved",
            final_reasoning="test",
            policy_version=1,
        )
    )
    db.commit()

    # Would previously raise IntegrityError (ForeignKeyViolation) here.
    seed(db, reset=True)

    reseeded_tenant = db.query(Tenant).filter(Tenant.name == "Northwind Outfitters").one()
    assert reseeded_tenant.id != tenant.id
    assert db.query(RefundRequest).filter(RefundRequest.tenant_id == tenant.id).count() == 0


def test_seed_is_idempotent_without_reset(db):
    seed(db, reset=False)
    tenants_after_first = db.query(Tenant).filter(Tenant.name == "Northwind Outfitters").count()

    seed(db, reset=False)  # should skip, not raise or duplicate
    tenants_after_second = db.query(Tenant).filter(Tenant.name == "Northwind Outfitters").count()

    assert tenants_after_first == 1
    assert tenants_after_second == 1


def test_seed_creates_a_customer_for_every_seed_row(db):
    seed(db, reset=False)

    tenant = db.query(Tenant).filter(Tenant.name == "Northwind Outfitters").one()
    customer_count = db.query(Customer).filter(Customer.tenant_id == tenant.id).count()

    assert customer_count == len(CUSTOMERS)
