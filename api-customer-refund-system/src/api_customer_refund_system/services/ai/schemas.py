"""The shape Claude is forced to respond in.

This class does double duty: it's the Pydantic model we validate the response
against, and `.model_json_schema()` is passed straight to the Anthropic API as a
tool definition. Because we set `tool_choice` to force this specific tool, the
model can't answer in free text - it can only fill in these typed fields. That's
what turns "parse whatever the model said" into "validate a JSON payload."
"""

from typing import Literal

from pydantic import BaseModel, Field

DecisionFlag = Literal[
    "suspicious_request",
    "policy_conflict",
    "missing_information",
    "high_value",
    "possible_injection_attempt",
]


class RefundRecommendation(BaseModel):
    decision: Literal["approve", "deny", "escalate"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(
        description="Plain-language explanation citing the specific policy rule(s) applied"
    )
    policy_rules_applied: list[str] = Field(
        default_factory=list,
        description="Rule identifiers from the policy document, e.g. ['final_sale_no_refund']",
    )
    flags: list[DecisionFlag] = Field(default_factory=list)
    recommended_amount: float | None = None
