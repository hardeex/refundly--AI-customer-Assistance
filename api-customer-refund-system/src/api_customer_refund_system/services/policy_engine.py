"""Deterministic policy enforcement.

This is the fourth and most important prompt-injection defense, and it's the
reason the AI is a recommender rather than a decision-maker: no matter what the
model outputs - even if a crafted message talked it into recommending "approve"
for a final-sale item - this module re-checks the hard rules in plain Python
before anything is persisted or returned to the caller. The model's job is
nuance; this module's job is that the $500 threshold is never actually crossed.
"""

from dataclasses import dataclass
from datetime import date

from api_customer_refund_system.services.ai.schemas import RefundRecommendation

DEFAULT_AUTO_APPROVE_CEILING = 500.0
DEFAULT_RETURN_WINDOW_DAYS = 30

# The AI's output uses a verb ("approve"/"deny"/"escalate" - see
# services.ai.schemas.RefundRecommendation), while refund_requests.status stores
# the resulting state as a noun ("approved"/"denied"/"escalated", matching the
# table's CHECK constraint). This is the one place that translates between them.
_DECISION_TO_STATUS = {"approve": "approved", "deny": "denied", "escalate": "escalated"}


@dataclass
class OrderFacts:
    order_date: date
    is_final_sale: bool


def order_age_days(order_date: date, as_of: date | None = None) -> int:
    as_of = as_of or date.today()
    return (as_of - order_date).days


def finalize_decision(
    recommendation: RefundRecommendation,
    order: OrderFacts,
    requested_amount: float | None,
    rules: dict,
) -> tuple[str, str]:
    """Apply the tenant's hard rules on top of the model's recommendation.

    Returns (final_decision, final_reasoning). Rule checks run in order and the
    first one that applies wins - each of these is a policy statement from
    section 1 of the refund policy that must hold regardless of what the AI said.
    """
    ceiling = rules.get("auto_approve_ceiling", DEFAULT_AUTO_APPROVE_CEILING)
    window_days = rules.get("return_window_days", DEFAULT_RETURN_WINDOW_DAYS)

    if order.is_final_sale:
        return (
            "denied",
            "Final sale items are not eligible for refunds under this policy.",
        )

    if requested_amount is not None and requested_amount > ceiling:
        reasoning = (
            f"Requested amount (${requested_amount:.2f}) exceeds the "
            f"${ceiling:.2f} threshold that requires human review."
        )
        return "escalated", reasoning

    age_days = order_age_days(order.order_date)
    if age_days > window_days:
        reasoning = (
            f"Order was placed {age_days} days ago, outside the "
            f"{window_days}-day return window."
        )
        return "denied", reasoning

    return _DECISION_TO_STATUS[recommendation.decision], recommendation.reasoning
