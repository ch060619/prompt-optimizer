from __future__ import annotations

from typing import Literal

# RC ID: RC-164. Map the user phrase "Claude Code format" to approved public interfaces only.

ClaudeIntegration = Literal["anthropic_messages", "official_agent_sdk"]
OfficialCredential = Literal["api_key", "oauth"]

_FORMAT_ALIASES: dict[str, ClaudeIntegration] = {
    "claude": "anthropic_messages",
    "claude_code": "anthropic_messages",
    "anthropic": "anthropic_messages",
    "anthropic_messages": "anthropic_messages",
    "official_agent_sdk": "official_agent_sdk",
    "anthropic_agent_sdk": "official_agent_sdk",
}
_FORBIDDEN_CREDENTIALS = {
    "cookie",
    "cookies",
    "subscription_token",
    "session_token",
    "internal_token",
    "claude_code_token",
}


def resolve_claude_code_format(value: str) -> ClaudeIntegration:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    try:
        return _FORMAT_ALIASES[normalized]
    except KeyError as exc:
        raise ValueError(
            "Claude Code 格式只能映射为 Anthropic Messages 或经批准的官方 Agent SDK。"
        ) from exc


def validate_claude_credential_kind(value: str) -> OfficialCredential:
    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in _FORBIDDEN_CREDENTIALS:
        raise ValueError("不接受 Claude Code 订阅 Cookie、内部令牌或未知会话凭据。")
    if normalized not in {"api_key", "oauth"}:
        raise ValueError("Claude 集成只接受服务商允许的官方 API Key 或 OAuth。")
    return normalized  # type: ignore[return-value]

