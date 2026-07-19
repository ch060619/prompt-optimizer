from __future__ import annotations

from dataclasses import dataclass

from .agent import AgentEvent, AgentEventType

# RC ID: RC-071. Aggregate ordered text, progress, tool, warning, and terminal events.


TERMINAL_EVENT_TYPES = frozenset(
    {
        AgentEventType.COMPLETED,
        AgentEventType.FAILED,
        AgentEventType.CANCELLED,
        AgentEventType.TERMINAL,
    }
)


@dataclass(frozen=True)
class StreamSummary:
    events: tuple[AgentEvent, ...]
    text: str
    terminal: AgentEventType | None


class StreamAccumulator:
    def __init__(self) -> None:
        self._events: list[AgentEvent] = []
        self._text: list[str] = []
        self._terminal: AgentEventType | None = None

    @property
    def events(self) -> tuple[AgentEvent, ...]:
        return tuple(self._events)

    @property
    def text(self) -> str:
        return "".join(self._text)

    @property
    def terminal(self) -> AgentEventType | None:
        return self._terminal

    def add(self, event: AgentEvent) -> None:
        if event.sequence != len(self._events):
            raise ValueError("Agent stream sequence is not contiguous")
        if self._terminal is not None:
            raise ValueError("Agent stream emitted events after a terminal event")
        self._events.append(event)
        if event.type is AgentEventType.DELTA and event.text:
            self._text.append(event.text)
        if event.type in TERMINAL_EVENT_TYPES:
            self._terminal = event.type

    def summary(self) -> StreamSummary:
        return StreamSummary(tuple(self._events), self.text, self.terminal)
