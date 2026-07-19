from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from prompt_optimizer.providers.base import ModelRequest, ProviderCapabilities

# RC ID: RC-078. Negotiate model capabilities before sending requests or tool schemas.


class CapabilityMismatch(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityRequirements:
    requires_text: bool = True
    wants_vision: bool = False
    requires_vision: bool = False
    wants_tools: bool = False
    requires_tools: bool = False
    requires_structured_output: bool = False
    requires_reasoning: bool = False
    context_tokens: int = 0


@dataclass(frozen=True)
class CapabilityPlan:
    allowed: bool
    missing: tuple[str, ...] = ()
    adaptations: tuple[str, ...] = ()
    suggestions: tuple[str, ...] = ()
    tools: tuple[Any, ...] = ()


@dataclass(frozen=True)
class PreparedModelRequest:
    request: ModelRequest
    tools: tuple[Any, ...]


class CapabilityNegotiator:
    def __init__(self, capabilities: ProviderCapabilities) -> None:
        self.capabilities = capabilities

    def negotiate(
        self,
        requirements: CapabilityRequirements,
        *,
        tools: Sequence[Any] = (),
    ) -> CapabilityPlan:
        missing: list[str] = []
        adaptations: list[str] = []
        suggestions: list[str] = []
        if requirements.requires_text and not self.capabilities.text:
            missing.append("text")
            suggestions.append("choose a text-capable model")
        if requirements.requires_vision and not self.capabilities.image:
            missing.append("vision")
            suggestions.append("remove images or choose a vision-capable model")
        if requirements.requires_structured_output and not self.capabilities.structured_output:
            missing.append("structured_output")
            suggestions.append("use plain text output and validate locally")
        if (
            self.capabilities.context_length is not None
            and requirements.context_tokens > self.capabilities.context_length
        ):
            missing.append("context_length")
            suggestions.append("compress context or choose a longer-context model")
        if requirements.requires_reasoning and not self.capabilities.reasoning:
            missing.append("reasoning")
            suggestions.append("use the model default reasoning mode")
        selected_tools: tuple[Any, ...] = ()
        if requirements.requires_tools and not self.capabilities.tools:
            missing.append("tools")
            suggestions.append("run without tools or choose a tool-capable model")
        elif requirements.wants_tools:
            if self.capabilities.tools:
                selected_tools = tuple(tools)
            else:
                adaptations.append("tools_disabled")
                suggestions.append("continue without tool calls")
        return CapabilityPlan(
            allowed=not missing,
            missing=tuple(missing),
            adaptations=tuple(adaptations),
            suggestions=tuple(suggestions),
            tools=selected_tools,
        )

    def prepare(self, request: ModelRequest, plan: CapabilityPlan) -> PreparedModelRequest:
        if not plan.allowed:
            missing = ", ".join(plan.missing)
            raise CapabilityMismatch(f"provider lacks required capabilities: {missing}")
        return PreparedModelRequest(request, plan.tools)
