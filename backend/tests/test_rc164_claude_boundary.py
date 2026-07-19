from __future__ import annotations

import pytest

from prompt_optimizer.providers import (
    resolve_claude_code_format,
    validate_claude_credential_kind,
)

# RC ID: RC-164. Reject unofficial Claude Code subscription credential paths.


def test_claude_code_format_maps_to_public_anthropic_interfaces() -> None:
    assert resolve_claude_code_format("Claude Code") == "anthropic_messages"
    assert resolve_claude_code_format("Anthropic Agent SDK") == "official_agent_sdk"
    assert validate_claude_credential_kind("API Key") == "api_key"
    assert validate_claude_credential_kind("OAuth") == "oauth"


@pytest.mark.parametrize(
    "value",
    ["cookie", "subscription-token", "session_token", "internal token", "unknown"],
)
def test_claude_boundary_rejects_subscription_or_unknown_credentials(value: str) -> None:
    with pytest.raises(ValueError, match="Claude"):
        validate_claude_credential_kind(value)


def test_claude_boundary_rejects_unknown_format() -> None:
    with pytest.raises(ValueError, match="Anthropic Messages"):
        resolve_claude_code_format("claude-code-private-protocol")
