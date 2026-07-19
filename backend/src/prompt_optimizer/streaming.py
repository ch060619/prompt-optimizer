from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from typing import Any

from pydantic import BaseModel, Field

# RC ID: RC-152. Keep optimization SSE replay independent from optional workspace packages.


class OptimizationStreamEventType(StrEnum):
    STARTED = "started"
    ANALYSIS = "analysis"
    DELTA = "delta"
    SAVED = "saved"
    FALLBACK = "fallback"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class OptimizationStreamEvent(BaseModel):
    protocol_version: str = "v1"
    request_id: str = Field(min_length=1)
    seq: int = Field(ge=0)
    type: OptimizationStreamEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OptimizationStreamCursor(BaseModel):
    request_id: str = Field(min_length=1)
    after_seq: int = Field(default=-1, ge=-1)


class OptimizationStreamCursorExpired(RuntimeError):
    pass


class OptimizationStreamClosed(RuntimeError):
    pass


class OptimizationStreamLog:
    def __init__(self, *, max_events: int | None = None) -> None:
        if max_events is not None and max_events < 1:
            raise ValueError("max_events 必须大于 0。")
        self._events: dict[str, list[OptimizationStreamEvent]] = {}
        self._next_seq: dict[str, int] = {}
        self._event_keys: dict[tuple[str, str], OptimizationStreamEvent] = {}
        self._cancelled: set[str] = set()
        self._max_events = max_events
        self._lock = Lock()

    def append(
        self,
        request_id: str,
        event_type: OptimizationStreamEventType,
        payload: dict[str, Any] | None = None,
        *,
        event_key: str | None = None,
    ) -> OptimizationStreamEvent:
        if not request_id:
            raise ValueError("request_id 不能为空。")
        with self._lock:
            if event_key is not None:
                existing = self._event_keys.get((request_id, event_key))
                if existing is not None:
                    return existing
            if (
                request_id in self._cancelled
                and event_type is not OptimizationStreamEventType.CANCELLED
            ):
                raise OptimizationStreamClosed("已取消的流不能继续追加业务事件。")
            sequence = self._next_seq.get(request_id, 0)
            event = OptimizationStreamEvent(
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
            if event_type is OptimizationStreamEventType.CANCELLED:
                self._cancelled.add(request_id)
            return event

    def replay(self, cursor: OptimizationStreamCursor) -> tuple[OptimizationStreamEvent, ...]:
        with self._lock:
            events = self._events.get(cursor.request_id, [])
            if events and cursor.after_seq < events[0].seq - 1:
                raise OptimizationStreamCursorExpired("重连游标已超出事件保留范围。")
            return tuple(event for event in events if event.seq > cursor.after_seq)

    def latest_seq(self, request_id: str) -> int:
        with self._lock:
            events = self._events.get(request_id, [])
            return events[-1].seq if events else -1

    def cancel(
        self,
        request_id: str,
        *,
        reason: str = "client_cancelled",
    ) -> OptimizationStreamEvent:
        return self.append(
            request_id,
            OptimizationStreamEventType.CANCELLED,
            {"reason": reason},
            event_key="cancel",
        )

    def is_cancelled(self, request_id: str) -> bool:
        with self._lock:
            return request_id in self._cancelled


def encode_optimization_sse(event: OptimizationStreamEvent) -> str:
    data = {
        **event.payload,
        "protocol_version": event.protocol_version,
        "request_id": event.request_id,
        "seq": event.seq,
        "type": event.type.value,
        "timestamp": event.timestamp.isoformat(),
    }
    encoded = json.dumps(data, ensure_ascii=False)
    return f"id: {event.seq}\nevent: {event.type.value}\ndata: {encoded}\n\n"
