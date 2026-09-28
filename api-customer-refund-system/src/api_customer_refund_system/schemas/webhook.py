import uuid

from pydantic import BaseModel, ConfigDict, HttpUrl


class WebhookCreate(BaseModel):
    url: HttpUrl


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    active: bool


class WebhookCreated(WebhookOut):
    # Only returned once, at creation time - never persisted in plaintext on read paths.
    secret: str
