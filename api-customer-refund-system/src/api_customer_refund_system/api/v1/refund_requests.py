"""Submit, fetch, and list refund requests.

Submitting a request is where the whole system comes together: it loads the
verified order/customer data, gets a recommendation from Claude, and then lets
the deterministic policy engine have the final say before anything is saved.
See services/policy_engine.py for why that last step isn't optional.
"""

import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy.orm import Session

from api_customer_refund_system.api.deps import get_current_tenant_id, get_db
from api_customer_refund_system.api.rate_limit import limiter
from api_customer_refund_system.models.customer import Customer
from api_customer_refund_system.models.decision_log import DecisionLog
from api_customer_refund_system.models.order import Order
from api_customer_refund_system.models.policy import RefundPolicy
from api_customer_refund_system.models.refund_request import RefundRequest
from api_customer_refund_system.models.tenant import Tenant
from api_customer_refund_system.models.webhook import Webhook
from api_customer_refund_system.schemas.refund_request import (
    RefundRequestCreate,
    RefundRequestListItem,
    RefundRequestOut,
)
from api_customer_refund_system.services.ai import prompts
from api_customer_refund_system.services.ai.client import get_recommendation
from api_customer_refund_system.services.policy_engine import OrderFacts, finalize_decision
from api_customer_refund_system.services.webhook_dispatcher import send_decision_webhook

router = APIRouter(prefix="/refund-requests", tags=["refund-requests"])


def _get_active_policy(db: Session, tenant_id: uuid.UUID) -> RefundPolicy:
    policy = (
        db.query(RefundPolicy)
        .filter(RefundPolicy.tenant_id == tenant_id, RefundPolicy.active.is_(True))
        .order_by(RefundPolicy.version.desc())
        .first()
    )
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active refund policy configured for this tenant",
        )
    return policy


def _serialize_customer(customer: Customer) -> dict:
    return {
        "id": str(customer.id),
        "name": customer.name,
        "email": customer.email,
        "signup_date": customer.signup_date,
        "risk_flag": customer.risk_flag,
    }


def _serialize_order(order: Order) -> dict:
    return {
        "id": str(order.id),
        "order_date": order.order_date,
        "total_amount": order.total_amount,
        "status": order.status,
        "is_final_sale": order.is_final_sale,
        "items": [
            {
                "sku": item.sku,
                "description": item.description,
                "price": item.price,
                "quantity": item.quantity,
            }
            for item in order.items
        ],
    }


def _to_refund_request_out(db: Session, refund_request: RefundRequest) -> RefundRequestOut:
    decision_log = (
        db.query(DecisionLog)
        .filter(DecisionLog.refund_request_id == refund_request.id)
        .order_by(DecisionLog.created_at.desc())
        .first()
    )
    return RefundRequestOut(
        id=refund_request.id,
        status=refund_request.status,
        reasoning=decision_log.final_reasoning if decision_log else "",
        policy_version=decision_log.policy_version if decision_log else 0,
        flags=decision_log.flags if decision_log else [],
        created_at=refund_request.created_at,
    )


@router.post("", response_model=RefundRequestOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def submit_refund_request(
    request: Request,
    payload: RefundRequestCreate,
    background_tasks: BackgroundTasks,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> RefundRequestOut:
    if idempotency_key:
        existing = (
            db.query(RefundRequest)
            .filter(
                RefundRequest.tenant_id == tenant_id,
                RefundRequest.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing is not None:
            return _to_refund_request_out(db, existing)

    customer = (
        db.query(Customer)
        .filter(Customer.id == payload.customer_id, Customer.tenant_id == tenant_id)
        .first()
    )
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    order = (
        db.query(Order).filter(Order.id == payload.order_id, Order.tenant_id == tenant_id).first()
    )
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.customer_id != customer.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Order does not belong to this customer"
        )

    policy = _get_active_policy(db, tenant_id)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    system_prompt = prompts.build_system_prompt(
        tenant_name=tenant.name if tenant else "this business",
        policy_text=policy.policy_text,
        policy_version=policy.version,
    )
    user_prompt = prompts.build_user_prompt(
        order=_serialize_order(order),
        customer=_serialize_customer(customer),
        requested_amount=payload.requested_amount,
        message=payload.message,
    )

    model_result = get_recommendation(system_prompt, user_prompt)

    final_decision, final_reasoning = finalize_decision(
        recommendation=model_result.recommendation,
        order=OrderFacts(order_date=order.order_date, is_final_sale=order.is_final_sale),
        requested_amount=payload.requested_amount,
        rules=policy.rules_json,
    )

    resolved_at = datetime.now(UTC)
    refund_request = RefundRequest(
        tenant_id=tenant_id,
        customer_id=customer.id,
        order_id=order.id,
        message=payload.message,
        requested_amount=payload.requested_amount,
        idempotency_key=idempotency_key,
        status=final_decision,
        resolved_at=resolved_at,
    )
    db.add(refund_request)
    db.flush()  # assigns refund_request.id ahead of the commit below

    decision_log = DecisionLog(
        refund_request_id=refund_request.id,
        model_used=model_result.model_used,
        prompt_snapshot=f"SYSTEM PROMPT:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}",
        raw_model_output=model_result.raw_output,
        final_decision=final_decision,
        final_reasoning=final_reasoning,
        policy_version=policy.version,
        flags=list(model_result.recommendation.flags),
        latency_ms=model_result.latency_ms,
    )
    db.add(decision_log)
    db.commit()
    db.refresh(refund_request)

    webhooks = (
        db.query(Webhook).filter(Webhook.tenant_id == tenant_id, Webhook.active.is_(True)).all()
    )
    for webhook in webhooks:
        background_tasks.add_task(
            send_decision_webhook,
            webhook.url,
            webhook.secret,
            {
                "event": "refund_request.resolved",
                "request_id": str(refund_request.id),
                "status": final_decision,
                "reasoning": final_reasoning,
                "timestamp": resolved_at.isoformat(),
            },
        )

    return RefundRequestOut(
        id=refund_request.id,
        status=final_decision,
        reasoning=final_reasoning,
        policy_version=policy.version,
        flags=list(model_result.recommendation.flags),
        created_at=refund_request.created_at,
    )


@router.get("/{refund_request_id}", response_model=RefundRequestOut)
def get_refund_request(
    refund_request_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> RefundRequestOut:
    refund_request = (
        db.query(RefundRequest)
        .filter(RefundRequest.id == refund_request_id, RefundRequest.tenant_id == tenant_id)
        .first()
    )
    if refund_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refund request not found"
        )
    return _to_refund_request_out(db, refund_request)


@router.get("", response_model=list[RefundRequestListItem])
def list_refund_requests(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[RefundRequestListItem]:
    query = db.query(RefundRequest).filter(RefundRequest.tenant_id == tenant_id)
    if status_filter:
        query = query.filter(RefundRequest.status == status_filter)
    refund_requests = query.order_by(RefundRequest.created_at.desc()).limit(limit).all()

    if not refund_requests:
        return []

    customer_ids = {r.customer_id for r in refund_requests}
    customers_by_id = {
        c.id: c for c in db.query(Customer).filter(Customer.id.in_(customer_ids)).all()
    }

    request_ids = [r.id for r in refund_requests]
    decision_logs = (
        db.query(DecisionLog)
        .filter(DecisionLog.refund_request_id.in_(request_ids))
        .order_by(DecisionLog.created_at.desc())
        .all()
    )
    latest_log_by_request: dict[uuid.UUID, DecisionLog] = {}
    for log in decision_logs:
        latest_log_by_request.setdefault(log.refund_request_id, log)

    items: list[RefundRequestListItem] = []
    for refund_request in refund_requests:
        log = latest_log_by_request.get(refund_request.id)
        customer = customers_by_id.get(refund_request.customer_id)
        items.append(
            RefundRequestListItem(
                id=refund_request.id,
                customer_id=refund_request.customer_id,
                customer_name=customer.name if customer else "Unknown customer",
                order_id=refund_request.order_id,
                message=refund_request.message,
                requested_amount=refund_request.requested_amount,
                status=refund_request.status,
                reasoning=log.final_reasoning if log else None,
                flags=log.flags if log else [],
                created_at=refund_request.created_at,
                resolved_at=refund_request.resolved_at,
            )
        )
    return items
