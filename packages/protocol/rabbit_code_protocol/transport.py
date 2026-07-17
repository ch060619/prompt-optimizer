"""Small, process-local transport primitives for the RC-063 boundary.

The event log is deliberately independent of FastAPI and provider code. It gives
SSE/WebSocket consumers one cursor and replay contract while later RCs decide
which storage and process-lifecycle implementation is appropriate.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from threading import Lock
from typing import Generic, TypeVar, cast

from .models import StreamCursor, StreamEvent, StreamEventType

# RC ID: RC-063. Keep reconnect, cancellation, and tool idempotency semantics in one boundary.

T = TypeVar("T")


class CursorExpiredError(RuntimeError):
    """Raised when a bounded event log no longer contains the requested cursor."""


class StreamClosedError(RuntimeError):
    """Raised when a non-cancellation event is appended after cancellation."""


class DuplicateToolExecutionError(RuntimeError):
    """Raised when the same tool call is concurrently executed twice."""


class StreamEventLog:
    """Assign monotonic sequence numbers and replay confirmed stream events."""

    def __init__(self, *, max_events: int | None = None) -> None:
        if max_events is not None and max_events < 1:
            raise ValueError("max_events 必须大于 0。")
        self._events: dict[str, list[StreamEvent]] = {}
        self._next_seq: dict[str, int] = {}
        self._event_keys: dict[tuple[str, str], StreamEvent] = {}
        self._cancelled: set[str] = set()
        self._max_events = max_events
        self._lock = Lock()

    def append(
        self,
        request_id: str,
        event_type: StreamEventType,
        payload: dict[str, object] | None = None,
        *,
        event_key: str | None = None,
    ) -> StreamEvent:
        if not request_id:
            raise ValueError("request_id 不能为空。")
        with self._lock:
            if event_key is not None:
                existing = self._event_keys.get((request_id, event_key))
                if existing is not None:
                    return existing
            if request_id in self._cancelled and event_type is not StreamEventType.CANCELLED:
                raise StreamClosedError("已取消的流不能继续追加业务事件。")
            sequence = self._next_seq.get(request_id, 0)
            event = StreamEvent(
                request_id=request_id,
                seq=sequence,
                type=event_type,
                payload=payload or {},
            )
            events = self._events.setdefault(request_id, [])
            events.append(event)
            self._next_seq[request_id] = sequence + 1
            if event_key is not None:
                self._event_keys[(request_id, event_key)] = event
            if self._max_events is not None and len(events) > self._max_events:
                events.pop(0)
            if event_type is StreamEventType.CANCELLED:
                self._cancelled.add(request_id)
            return event

    def replay(self, cursor: StreamCursor) -> tuple[StreamEvent, ...]:
        with self._lock:
            events = self._events.get(cursor.request_id, [])
            if events and cursor.after_seq < events[0].seq - 1:
                raise CursorExpiredError("重连游标已超出事件保留范围。")
            return tuple(event for event in events if event.seq > cursor.after_seq)

    def latest_cursor(self, request_id: str) -> StreamCursor:
        with self._lock:
            events = self._events.get(request_id, [])
            after_seq = events[-1].seq if events else -1
            return StreamCursor(request_id=request_id, after_seq=after_seq)

    def cancel(self, request_id: str, *, reason: str = "client_cancelled") -> StreamEvent:
        return self.append(
            request_id,
            StreamEventType.CANCELLED,
            {"reason": reason},
            event_key="cancel",
        )

    def is_cancelled(self, request_id: str) -> bool:
        with self._lock:
            return request_id in self._cancelled


class ToolExecutionLedger(Generic[T]):
    """Cache completed tool calls so reconnect retries cannot execute them twice."""

    def __init__(self) -> None:
        self._completed: dict[tuple[str, str], T] = {}
        self._in_flight: set[tuple[str, str]] = set()
        self._lock = Lock()

    def execute(
        self,
        request_id: str,
        call_id: str,
        operation: Callable[[], T],
    ) -> T:
        if not request_id or not call_id:
            raise ValueError("request_id 和 call_id 不能为空。")
        key = (request_id, call_id)
        with self._lock:
            if key in self._completed:
                return self._completed[key]
            if key in self._in_flight:
                raise DuplicateToolExecutionError("工具调用正在执行，不能并发重试。")
            self._in_flight.add(key)
        completed = False
        result: T | None = None
        try:
            result = operation()
            completed = True
            return result
        finally:
            with self._lock:
                self._in_flight.remove(key)
                if completed:
                    self._completed[key] = cast(T, result)


def encode_sse(event: StreamEvent) -> str:
    """Encode a protocol event with a resumable SSE id."""

    data = json.dumps(event.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"))
    return f"id: {event.seq}\nevent: {event.type.value}\ndata: {data}\n\n"


def encode_sse_heartbeat() -> str:
    """Return an SSE comment that keeps an idle connection alive."""

    return ": heartbeat\n\n"
