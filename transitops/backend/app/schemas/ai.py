"""AI settings + chat/advisor schemas (docs/03 §4 AI, docs/06)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AISettingsPublic(BaseModel):
    # `model` is a plain field name; disable the protected-namespace guard.
    model_config = ConfigDict(protected_namespaces=())

    chatbot_enabled: bool
    model: str


class AISettingsFull(AISettingsPublic):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    temperature: Decimal
    max_tokens: int
    system_prompt: str
    role_tool_permissions: dict
    updated_at: datetime


class AISettingsUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    chatbot_enabled: bool | None = None
    model: str | None = Field(default=None, min_length=1, max_length=80)
    temperature: Decimal | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=128, le=8192)
    system_prompt: str | None = Field(default=None, max_length=4000)
    role_tool_permissions: dict | None = None


# --- chat (BE-14) ---

class ChatRequest(BaseModel):
    session_id: uuid.UUID | None = None
    message: str = Field(min_length=1)


class ToolCallOut(BaseModel):
    tool: str
    args: dict


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    reply: str
    tool_calls: list[ToolCallOut] = []


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    tool_calls: dict | list | None = None
    created_at: datetime


# --- trip advisor (BE-15) ---

class TripAdvisorRequest(BaseModel):
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID
    cargo_weight_kg: Decimal = Field(gt=0)
    planned_distance_km: Decimal = Field(gt=0)


class TripAdvisorResponse(BaseModel):
    verdict: Literal["go", "caution", "block"]
    hard_failures: list[str]
    risk_factors: list[str]
    summary: str
