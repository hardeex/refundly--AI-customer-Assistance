"""Unit tests for the deterministic policy engine - no database, no network.

These are the tests that matter most for the "the AI never gets the final
word" claim in the README: each one hands finalize_decision a model
recommendation that says the *wrong* thing, and checks the hard rule wins
anyway.
"""

from datetime import date, timedelta

from api_customer_refund_system.services.ai.schemas import RefundRecommendation
from api_customer_refund_system.services.policy_engine import OrderFacts, finalize_decision

RULES = {"auto_approve_ceiling": 500, "return_window_days": 30}


def _model_recommends(decision: str, **overrides) -> RefundRecommendation:
    fields = {"decision": decision, "confidence": 0.9, "reasoning": "model said so"}
    fields.update(overrides)
    return RefundRecommendation(**fields)


def test_final_sale_is_denied_even_when_model_approves():
    order = OrderFacts(order_date=date.today(), is_final_sale=True)

    status, _ = finalize_decision(_model_recommends("approve"), order, 50.0, RULES)

    assert status == "denied"


def test_amount_over_ceiling_is_escalated_even_when_model_approves():
    order = OrderFacts(order_date=date.today(), is_final_sale=False)

    status, _ = finalize_decision(_model_recommends("approve"), order, 650.0, RULES)

    assert status == "escalated"


def test_amount_at_ceiling_does_not_trigger_escalation():
    order = OrderFacts(order_date=date.today(), is_final_sale=False)

    status, _ = finalize_decision(_model_recommends("approve"), order, 500.0, RULES)

    assert status == "approved"


def test_order_past_return_window_is_denied_even_when_model_approves():
    order = OrderFacts(order_date=date.today() - timedelta(days=31), is_final_sale=False)

    status, _ = finalize_decision(_model_recommends("approve"), order, 50.0, RULES)

    assert status == "denied"


def test_order_at_exactly_the_window_boundary_is_not_denied():
    order = OrderFacts(order_date=date.today() - timedelta(days=30), is_final_sale=False)

    status, _ = finalize_decision(_model_recommends("approve"), order, 50.0, RULES)

    assert status == "approved"


def test_model_recommendation_passes_through_when_no_hard_rule_applies():
    order = OrderFacts(order_date=date.today() - timedelta(days=5), is_final_sale=False)

    status, reasoning = finalize_decision(
        _model_recommends("escalate", reasoning="ambiguous claim, needs a human"),
        order,
        50.0,
        RULES,
    )

    assert status == "escalated"
    assert reasoning == "ambiguous claim, needs a human"


def test_prompt_injection_flag_does_not_bypass_the_final_sale_rule():
    """Simulates a model that was talked into recommending approval - the flag
    alone changes nothing; the deterministic rule still wins."""
    order = OrderFacts(order_date=date.today(), is_final_sale=True)
    recommendation = _model_recommends("approve", flags=["possible_injection_attempt"])

    status, reasoning = finalize_decision(recommendation, order, 999.0, RULES)

    assert status == "denied"
    assert "final sale" in reasoning.lower()


def test_tenant_specific_rules_override_the_defaults():
    tight_rules = {"auto_approve_ceiling": 100, "return_window_days": 7}
    order = OrderFacts(order_date=date.today(), is_final_sale=False)

    status, _ = finalize_decision(_model_recommends("approve"), order, 150.0, tight_rules)

    assert status == "escalated"
