"""Register a callback URL that receives a signed POST whenever a refund request
resolves. See services/webhook_dispatcher.py for how delivery and signing work.
"""

import secrets
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api_customer_refund_system.api.deps import get_current_tenant_id, get_db
from api_customer_refund_system.models.webhook import Webhook
from api_customer_refund_system.schemas.webhook import WebhookCreate, WebhookCreated

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookCreated, status_code=status.HTTP_201_CREATED)
def register_webhook(
    payload: WebhookCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
) -> WebhookCreated:
    secret = secrets.token_urlsafe(32)
    webhook = Webhook(tenant_id=tenant_id, url=str(payload.url), secret=secret, active=True)
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return WebhookCreated(id=webhook.id, url=webhook.url, active=webhook.active, secret=secret)
