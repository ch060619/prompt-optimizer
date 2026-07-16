#!/usr/bin/env python3
"""RC ID: RC-018. Original synthetic boundary prototype for research only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

SYNTHETIC_KINDS: Final = {
    "synthetic.text.delta": "text_delta",
    "synthetic.tool.started": "tool_started",
    "synthetic.tool.finished": "tool_finished",
}


@dataclass(frozen=True)
class NeutralEvent:
    """Rabbit Code-neutral event; synthetic input names are intentionally original."""

    kind: str
    value: str


def translate_synthetic_event(kind: str, value: str) -> NeutralEvent:
    """Demonstrate an isolated boundary without importing any upstream package."""
    try:
        neutral_kind = SYNTHETIC_KINDS[kind]
    except KeyError as exc:
        raise ValueError(f"unsupported synthetic event: {kind}") from exc
    return NeutralEvent(kind=neutral_kind, value=value)


def main() -> None:
    events = [
        translate_synthetic_event("synthetic.text.delta", "draft"),
        translate_synthetic_event("synthetic.tool.started", "search"),
        translate_synthetic_event("synthetic.tool.finished", "2 results"),
    ]
    assert [event.kind for event in events] == ["text_delta", "tool_started", "tool_finished"]
    assert events[0].value == "draft"
    print("Synthetic boundary prototype passed: 3 events translated without upstream imports.")


if __name__ == "__main__":
    main()
