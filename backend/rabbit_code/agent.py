from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from threading import Event
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from prompt_optimizer.contracts import Provider
from prompt_optimizer.providers.base import ModelRequest, ProviderEvent, ProviderEventType
from prompt_optimizer.providers.capabilities import (
    CapabilitySnapshot,
    ProviderCapabilityResolver,
)

from .agent_state import (
    AgentState,
    AgentStateMachine,
    CheckpointStore,
    InMemoryCheckpointStore,
)
from .budget import BudgetController
from .capabilities import CapabilityMismatch, CapabilityNegotiator, CapabilityRequirements
from .run_control import (
    IdempotencyLedger,
    OperationKind,
    RunCancelled,
    RunCommand,
    RunController,
    RunStatus,
)

# RC ID: RC-057. Keep the candidate Agent Core independent from API and CLI presentation.
# RC ID: RC-068. Map provider output through the observable Agent state machine.
# RC ID: RC-167. Gate optional request features with the resolved Provider contract.


class AgentEventType(StrEnum):
    STARTED = "started"
    DELTA = "delta"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    PROGRESS = "progress"
    TOOL_CARD = "tool_card"
    TASK_PROGRESS = "task_progress"
    WARNING = "warning"
    TERMINAL = "terminal"


@dataclass(frozen=True)
class AgentEvent:
    type: AgentEventType
    text: str | None = None
    sequence: int = 0
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "text": self.text,
            "seq": self.sequence,
            "payload": dict(self.payload),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> AgentEvent:
        raw_type = value.get("type")
        try:
            event_type = AgentEventType(str(raw_type))
            payload = value.get("payload")
            normalized_payload = dict(payload) if isinstance(payload, Mapping) else {}
        except ValueError:
            event_type = AgentEventType.TERMINAL
            normalized_payload = {
                "unknown_event_type": str(raw_type),
                "original_payload": value.get("payload", {}),
            }
        raw_sequence = value.get("seq", value.get("sequence", 0))
        sequence = raw_sequence if isinstance(raw_sequence, int) else 0
        raw_text = value.get("text")
        return cls(
            event_type,
            text=raw_text if isinstance(raw_text, str) else None,
            sequence=sequence,
            payload=normalized_payload,
        )


class AgentCore:
    def __init__(
        self,
        provider: Provider,
        checkpoint_store: CheckpointStore | None = None,
        budget: BudgetController | None = None,
        run_control: RunController | None = None,
        idempotency_ledger: IdempotencyLedger | None = None,
        capability_resolver: ProviderCapabilityResolver | None = None,
    ) -> None:
        self.provider = provider
        self.checkpoint_store = checkpoint_store or InMemoryCheckpointStore()
        self.budget = budget
        self.run_control = run_control
        self.idempotency_ledger = idempotency_ledger or IdempotencyLedger()
        self.capability_resolver = capability_resolver or ProviderCapabilityResolver()

    def capabilities(self, *, force: bool = False) -> CapabilitySnapshot:
        return self.capability_resolver.resolve(self.provider, force=force)

    def _prepare_request(self, request: ModelRequest) -> ModelRequest:
        snapshot = self.capabilities()
        plan = CapabilityNegotiator(snapshot.capabilities).negotiate(
            CapabilityRequirements(
                wants_tools=bool(request.tools),
                requires_structured_output=request.response_format is not None,
            ),
            tools=request.tools,
        )
        if not plan.allowed:
            missing = ", ".join(plan.missing)
            raise CapabilityMismatch(f"provider lacks required capabilities: {missing}")
        if request.tools and not plan.tools:
            return replace(request, tools=())
        return request

    def stream(
        self,
        request: ModelRequest,
        cancellation: Event | None = None,
        request_id: str | None = None,
        run_control: RunController | None = None,
    ) -> Iterator[AgentEvent]:
        machine = AgentStateMachine(request_id or uuid4().hex, self.checkpoint_store)
        sequence = 0
        budget_started = False
        control = run_control or self.run_control

        def emit(
            event_type: AgentEventType,
            text: str | None = None,
            payload: Mapping[str, Any] | None = None,
        ) -> AgentEvent:
            nonlocal sequence
            event = AgentEvent(event_type, text, sequence, payload or {})
            sequence += 1
            return event

        try:
            yield emit(AgentEventType.STARTED)
            if control is not None:
                control.check()
            machine.transition(AgentState.CONTEXT)
            if cancellation and cancellation.is_set():
                machine.transition(AgentState.CANCELLED)
                yield emit(AgentEventType.CANCELLED)
                return
            if self.budget is not None:
                notices = self.budget.start_round(
                    input_tokens=max(1, len(request.prompt) // 4),
                    context_tokens=len(request.prompt),
                )
                budget_started = True
                for notice in notices:
                    yield emit(
                        AgentEventType.WARNING,
                        text=notice.message,
                        payload={
                            "budget_dimension": notice.dimension,
                            "used": notice.used,
                            "limit": notice.limit,
                        },
                    )
            machine.transition(AgentState.MODEL)
            prepared_request = self._prepare_request(request)
            model_key = f"{machine.run_id}:model"
            provider_events = self.idempotency_ledger.execute_stream(
                model_key,
                OperationKind.MODEL,
                lambda: self.provider.stream(prepared_request),
            )
            provider_completed = False
            for raw_provider_event in provider_events:
                provider_event = _coerce_provider_event(raw_provider_event)
                if provider_completed:
                    continue
                if control is not None:
                    control.check()
                if self.budget is not None:
                    self.budget.check_wall_clock()
                if cancellation and cancellation.is_set():
                    machine.transition(AgentState.CANCELLED)
                    yield emit(AgentEventType.CANCELLED)
                    return
                if provider_event.type is ProviderEventType.DELTA and provider_event.text:
                    if self.budget is not None:
                        notices = self.budget.record_output(
                            output_tokens=max(1, len(provider_event.text) // 4)
                        )
                        for notice in notices:
                            yield emit(
                                AgentEventType.WARNING,
                                text=notice.message,
                                payload={
                                    "budget_dimension": notice.dimension,
                                    "used": notice.used,
                                    "limit": notice.limit,
                                },
                            )
                    yield emit(AgentEventType.DELTA, text=provider_event.text)
                elif provider_event.type is ProviderEventType.COMPLETED:
                    machine.transition(AgentState.COMPLETED)
                    if control is not None:
                        control.mark_completed()
                    yield emit(AgentEventType.COMPLETED)
                    provider_completed = True
            if not provider_completed:
                raise RuntimeError("provider stream ended without a completed event")
            return
        except RunCancelled:
            machine.transition(AgentState.CANCELLED)
            if control is not None and control.status is not RunStatus.CANCELLED:
                control.command(RunCommand.CANCEL)
            yield emit(AgentEventType.CANCELLED)
        except Exception as exc:
            if control is not None:
                control.mark_failed()
            if machine.state not in {
                AgentState.COMPLETED,
                AgentState.FAILED,
                AgentState.CANCELLED,
            }:
                machine.transition(AgentState.FAILED, {"error": str(exc)})
            yield emit(AgentEventType.FAILED, text=str(exc), payload={"error": str(exc)})
        finally:
            if budget_started and self.budget is not None:
                self.budget.finish_round()
            if machine.state not in {
                AgentState.COMPLETED,
                AgentState.FAILED,
                AgentState.CANCELLED,
            }:
                machine.transition(AgentState.CANCELLED, {"reason": "stream closed"})
                if control is not None and control.status not in {
                    RunStatus.COMPLETED,
                    RunStatus.FAILED,
                    RunStatus.CANCELLED,
                }:
                    control.command(RunCommand.CANCEL)


def _coerce_provider_event(value: Any) -> ProviderEvent:
    if isinstance(value, ProviderEvent):
        return value
    if isinstance(value, Mapping):
        return ProviderEvent(
            ProviderEventType(value["type"]),
            text=value.get("text"),
        )
    raise TypeError(f"invalid provider event: {type(value).__name__}")
