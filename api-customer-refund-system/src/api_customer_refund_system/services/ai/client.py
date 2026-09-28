"""Thin wrapper around the Anthropic API. This is the only module in the codebase
allowed to talk to Anthropic - everything else works with the typed
RefundRecommendation it returns, never with raw model output.
"""

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import anthropic

from api_customer_refund_system.core.config import get_settings
from api_customer_refund_system.services.ai.schemas import RefundRecommendation

TOOL_NAME = "submit_refund_recommendation"


@lru_cache
def _get_client() -> anthropic.Anthropic:
    settings = get_settings()
    return anthropic.Anthropic(
        api_key=settings.anthropic_api_key, timeout=settings.anthropic_timeout
    )


@dataclass
class ModelResult:
    recommendation: RefundRecommendation
    raw_output: dict[str, Any]
    model_used: str
    latency_ms: int


def get_recommendation(system_prompt: str, user_prompt: str) -> ModelResult:
    settings = get_settings()
    client = _get_client()

    started_at = time.monotonic()
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=system_prompt,
        tools=[
            {
                "name": TOOL_NAME,
                "description": "Submit a structured refund recommendation.",
                "input_schema": RefundRecommendation.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": user_prompt}],
    )
    latency_ms = int((time.monotonic() - started_at) * 1000)

    tool_call = next(block for block in response.content if block.type == "tool_use")
    recommendation = RefundRecommendation.model_validate(tool_call.input)

    return ModelResult(
        recommendation=recommendation,
        raw_output=tool_call.input,
        model_used=settings.anthropic_model,
        latency_ms=latency_ms,
    )
