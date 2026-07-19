from __future__ import annotations

import pytest
from backend.rabbit_code.capabilities import (
    CapabilityMismatch,
    CapabilityNegotiator,
    CapabilityRequirements,
)

from prompt_optimizer.providers.base import ModelRequest, ProviderCapabilities

# RC ID: RC-078. Verify capability negotiation, fallback plans, and tool-schema gating.


def test_negotiator_adapts_optional_tools_and_never_sends_unsupported_schema() -> None:
    negotiator = CapabilityNegotiator(
        ProviderCapabilities(text=True, tools=False, context_length=100)
    )

    plan = negotiator.negotiate(
        CapabilityRequirements(wants_tools=True, context_tokens=20),
        tools=("read_file schema",),
    )
    prepared = negotiator.prepare(ModelRequest(prompt="测试"), plan)

    assert plan.allowed
    assert "tools_disabled" in plan.adaptations
    assert prepared.tools == ()


def test_required_capability_is_rejected_with_alternative_suggestion() -> None:
    negotiator = CapabilityNegotiator(ProviderCapabilities(text=True, tools=False))

    plan = negotiator.negotiate(CapabilityRequirements(requires_tools=True))

    assert not plan.allowed
    assert "tools" in plan.missing
    assert plan.suggestions
    with pytest.raises(CapabilityMismatch, match="tools"):
        negotiator.prepare(ModelRequest(prompt="必须使用工具"), plan)


def test_context_and_reasoning_requirements_are_checked() -> None:
    negotiator = CapabilityNegotiator(
        ProviderCapabilities(text=True, reasoning=False, context_length=10)
    )

    plan = negotiator.negotiate(
        CapabilityRequirements(context_tokens=11, requires_reasoning=True)
    )

    assert not plan.allowed
    assert plan.missing == ("context_length", "reasoning")
