"""Signs and delivers decision events to a tenant's registered webhook endpoints.

Delivery here is best-effort and synchronous (called from a FastAPI background
task after the response has already gone out to the caller). A production
version would persist a delivery queue and retry with backoff instead of
dropping a failed POST on the floor - noted as a trade-off in the README
rather than built out, since it wasn't the priority for this iteration.
"""

import hashlib
import hmac
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT_SECONDS = 5.0


def sign_payload(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def send_decision_webhook(url: str, secret: str, event: dict[str, Any]) -> None:
    body = json.dumps(event).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Refundly-Signature": sign_payload(body, secret),
    }
    try:
        httpx.post(url, content=body, headers=headers, timeout=WEBHOOK_TIMEOUT_SECONDS)
    except httpx.HTTPError:
        logger.warning("Webhook delivery to %s failed", url, exc_info=True)
