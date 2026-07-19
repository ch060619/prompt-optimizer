from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Any

from packages.protocol.rabbit_code_protocol import ApprovalRequest

from prompt_optimizer.providers.base import ModelRequest  # type: ignore[import-untyped]

from .agent import AgentEvent, AgentEventType
from .runtime import AgentRuntime

# RC ID: RC-101. Render a compact Rabbit Code terminal interaction surface.


@dataclass
class TuiState:
    prompt: str = ""
    output: list[str] = field(default_factory=list)
    tool_status: str = "idle"
    permission_prompt: str | None = None
    approval_request: ApprovalRequest | None = None
    plan: list[str] = field(default_factory=list)
    diff: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    status: str = "idle"

    def apply(self, event: AgentEvent) -> None:
        self.status = event.type.value
        if event.type is AgentEventType.DELTA and event.text:
            self.output.append(event.text)
        payload = dict(event.payload)
        tool_name = payload.get("tool") or payload.get("name")
        if event.type is AgentEventType.TOOL_CARD or tool_name:
            tool_status = payload.get("status", event.type.value)
            self.tool_status = f"{tool_name or 'tool'}: {tool_status}"
        permission = payload.get("permission") or payload.get("approval")
        if payload.get("permission_required") or payload.get("approval_required"):
            self.permission_prompt = str(permission or "approval required")
        raw_approval_request = payload.get("approval_request")
        if isinstance(raw_approval_request, dict):
            try:
                self.approval_request = ApprovalRequest.model_validate(raw_approval_request)
            except ValueError:
                self.approval_request = None
        raw_plan = payload.get("plan")
        if isinstance(raw_plan, list):
            self.plan = [str(item) for item in raw_plan]
        raw_diff = payload.get("diff")
        if isinstance(raw_diff, str):
            self.diff = raw_diff
        raw_usage = payload.get("usage")
        if isinstance(raw_usage, dict):
            self.usage = {str(key): value for key, value in raw_usage.items()}
        if event.type in {
            AgentEventType.COMPLETED,
            AgentEventType.CANCELLED,
            AgentEventType.FAILED,
        }:
            self.permission_prompt = None
            self.approval_request = None


class TuiRenderer:
    @staticmethod
    def render(state: TuiState, *, width: int = 80, height: int = 24) -> str:
        if width < 24:
            raise ValueError("TUI width must be at least 24")
        if height < 8:
            raise ValueError("TUI height must be at least 8")
        lines = [
            _fit(f"Rabbit Code | {state.status}", width),
            _fit(f"Tool: {state.tool_status}", width),
        ]
        if state.permission_prompt:
            lines.append(_fit(f"Approval: {state.permission_prompt}", width))
        if state.approval_request:
            request = state.approval_request
            lines.append(_fit(f"Tool: {request.tool}", width))
            lines.append(_fit(f"Command: {' '.join(request.command)}", width))
            lines.append(_fit(f"Workdir: {request.workdir}", width))
            lines.append(_fit(f"Impact: {request.impact}", width))
        if state.plan:
            lines.append(_fit("Plan: " + " | ".join(state.plan), width))
        if state.diff:
            lines.extend(_wrapped("Diff: " + state.diff, width))
        if state.usage:
            usage = ", ".join(f"{key}={value}" for key, value in sorted(state.usage.items()))
            lines.append(_fit(f"Usage: {usage}", width))
        lines.append("-" * width)
        output_lines = _wrapped("".join(state.output), width)
        available = max(height - len(lines) - 2, 0)
        lines.extend(output_lines[:available])
        lines.append("-" * width)
        lines.append(_fit(f"> {state.prompt}", width))
        return "\n".join(lines)


class TuiSession:
    def __init__(self, runtime: AgentRuntime) -> None:
        self.runtime = runtime
        self.state = TuiState()

    def submit(self, prompt: str) -> TuiState:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        self.state.prompt = prompt
        for event in self.runtime.stream(ModelRequest(prompt=prompt)):
            self.state.apply(event)
        return self.state

    def render(self, *, width: int = 80, height: int = 24) -> str:
        return TuiRenderer.render(self.state, width=width, height=height)


def _wrapped(value: str, width: int) -> list[str]:
    if not value:
        return [""]
    return [line[:width] for line in textwrap.wrap(value, width=width) or [""]]


def _fit(value: str, width: int) -> str:
    return value[:width]
