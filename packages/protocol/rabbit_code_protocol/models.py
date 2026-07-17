from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

# RC ID: RC-061. Define versioned cross-surface request, event, task, and capability schemas.

ProtocolVersion = Literal["v1"]


class ProtocolModel(BaseModel):
    protocol_version: ProtocolVersion = "v1"


class TextBlock(ProtocolModel):
    type: Literal["text"] = "text"
    text: str


class ToolCallBlock(ProtocolModel):
    type: Literal["tool_call"] = "tool_call"
    call_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(ProtocolModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: list[TextBlock | ToolCallBlock] = Field(min_length=1)


class Session(ProtocolModel):
    session_id: str = Field(min_length=1)
    title: str | None = None
    status: Literal["active", "paused", "completed", "cancelled"] = "active"
    provider: str | None = None
    model: str | None = None


class AgentRequest(ProtocolModel):
    request_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: Message
    provider: str | None = None
    model: str | None = None


class ApprovalRequest(ProtocolModel):
    approval_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    description: str
    risk: Literal["low", "medium", "high"]


class StreamEventType(StrEnum):
    STARTED = "started"
    DELTA = "delta"
    TOOL_CALL = "tool_call"
    APPROVAL_REQUIRED = "approval_required"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class StreamEvent(ProtocolModel):
    request_id: str = Field(min_length=1)
    seq: int = Field(ge=0)
    type: StreamEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DiffPayload(ProtocolModel):
    old_revision: str = Field(min_length=1)
    new_revision: str = Field(min_length=1)
    lines: list[str]
    score_delta: float | None = None


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskEnvelope(ProtocolModel):
    task_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    status: TaskStatus
    result: dict[str, Any] | None = None
    error: ProtocolError | None = None


class ProtocolErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    PROVIDER_ERROR = "provider_error"
    CANCELLED = "cancelled"
    INTERNAL = "internal"


class ProtocolError(ProtocolModel):
    code: ProtocolErrorCode
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ProviderCapabilities(ProtocolModel):
    text: bool = True
    streaming: bool = False
    images: bool = False
    tools: bool = False
    structured_output: bool = False
    context_length: int | None = Field(default=None, ge=1)
    model_listing: bool = False
    token_usage: bool = False
    cost_info: bool = False
