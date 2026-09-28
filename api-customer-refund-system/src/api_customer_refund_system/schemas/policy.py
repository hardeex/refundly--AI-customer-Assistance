import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PolicyCreate(BaseModel):
    rules_json: dict[str, Any] = Field(
        description=(
            "Hard, machine-checkable thresholds, e.g. "
            '{"auto_approve_ceiling": 500, "return_window_days": 30}'
        )
    )
    policy_text: str = Field(description="Prose policy shown to the AI model as context")


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    rules_json: dict[str, Any]
    policy_text: str
    active: bool
    created_at: datetime
