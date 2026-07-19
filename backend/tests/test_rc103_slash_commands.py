from __future__ import annotations

import pytest
from backend.rabbit_code.slash_commands import (
    SlashArgument,
    SlashCommandError,
    SlashCommandRegistry,
    SlashCommandSpec,
    UnknownSlashCommand,
    default_slash_registry,
)

# RC ID: RC-103. Verify default slash registry, help, completion, suggestions, and dispatch.


def test_default_commands_generate_help_and_completion() -> None:
    registry = default_slash_registry()
    help_text = registry.help()

    for name in (
        "help",
        "model",
        "provider",
        "permission",
        "plan",
        "context",
        "session",
        "clear",
        "compact",
        "mcp",
        "plugin",
        "doctor",
        "exit",
    ):
        assert f"/{name}" in help_text
    assert registry.complete("/p") == ("/permission", "/plan", "/plugin", "/provider")


def test_command_arguments_and_session_scope_are_enforced() -> None:
    registry = default_slash_registry()
    assert registry.parse('/model "gpt test"').arguments == ("gpt test",)
    assert registry.dispatch("/clear").affects_session
    assert registry.dispatch("/doctor").affects_session is False
    with pytest.raises(ValueError, match="requires"):
        registry.parse("/model")
    with pytest.raises(ValueError, match="at most"):
        registry.parse("/model one two")


def test_unknown_commands_offer_a_suggestion_and_exit_is_structured() -> None:
    registry = default_slash_registry()
    with pytest.raises(UnknownSlashCommand, match="did you mean /help"):
        registry.parse("/hlep")
    result = registry.dispatch("/exit")
    assert result.exit_requested
    assert result.affects_session is False


def test_custom_command_registry_rejects_duplicates_and_handles_quotes() -> None:
    registry = SlashCommandRegistry()
    registry.register(
        SlashCommandSpec(
            "echo",
            "Echo one value",
            (SlashArgument("value", required=True),),
        )
    )
    with pytest.raises(SlashCommandError, match="already"):
        registry.register(SlashCommandSpec("echo", "Duplicate"))
    assert registry.parse('/echo "hello world"').arguments == ("hello world",)
