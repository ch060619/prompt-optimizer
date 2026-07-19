from __future__ import annotations

from importlib.resources import files

SYSTEM_PROMPT_VERSION = "rc153.v1"
_SYSTEM_PROMPT_RESOURCE = "rc153.v1.txt"


def load_system_prompt(version: str = SYSTEM_PROMPT_VERSION) -> str:
    if version != SYSTEM_PROMPT_VERSION:
        raise ValueError(f"Unsupported system prompt version: {version}")
    return (
        files("prompt_optimizer.prompts")
        .joinpath(_SYSTEM_PROMPT_RESOURCE)
        .read_text(encoding="utf-8")
        .strip()
    )


SYSTEM_PROMPT = load_system_prompt()
