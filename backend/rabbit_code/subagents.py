from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from threading import Event, Lock
from types import MappingProxyType
from typing import Any

from .budget import BudgetController, BudgetExceeded, BudgetLimits
from .permissions import PermissionMode

# RC ID: RC-074. Bound child Agent inputs, permissions, budgets, depth, and concurrency.


class SubAgentLimitError(ValueError):
    pass


class SubAgentState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class SubAgentSpec:
    task_id: str
    prompt: str
    context: Mapping[str, Any]
    permission: PermissionMode = PermissionMode.PLAN
    budget: BudgetLimits | None = None
    depth: int = 1

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id is required")
        if not self.prompt:
            raise ValueError("prompt is required")
        if self.depth < 1:
            raise ValueError("depth must be positive")
        object.__setattr__(
            self,
            "context",
            MappingProxyType(deepcopy(dict(self.context))),
        )


@dataclass(frozen=True)
class SubAgentInput:
    spec: SubAgentSpec
    context: Mapping[str, Any]
    budget: BudgetController
    cancellation: Event

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "context",
            MappingProxyType(deepcopy(dict(self.context))),
        )


@dataclass(frozen=True)
class SubAgentResult:
    task_id: str
    state: SubAgentState
    output: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class SubAgentEvent:
    sequence: int
    task_id: str
    state: SubAgentState


@dataclass(frozen=True)
class SubAgentSummary:
    results: tuple[SubAgentResult, ...]
    merged_output: str
    failed_task_ids: tuple[str, ...]


class SubAgentManager:
    def __init__(
        self,
        executor: Callable[[SubAgentInput], str],
        *,
        parent_permission: PermissionMode = PermissionMode.PLAN,
        parent_budget: BudgetController | None = None,
        default_budget: BudgetLimits | None = None,
        max_depth: int = 1,
        max_concurrency: int = 1,
    ) -> None:
        if max_depth < 1:
            raise ValueError("max_depth must be positive")
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self.executor = executor
        self.parent_permission = parent_permission
        self.parent_budget = parent_budget
        self.default_budget = default_budget or BudgetLimits(max_rounds=1)
        self.max_depth = max_depth
        self.max_concurrency = max_concurrency
        self._cancel = Event()
        self._lock = Lock()
        self._events: list[SubAgentEvent] = []
        self._active = 0
        self._peak_concurrency = 0

    @property
    def events(self) -> tuple[SubAgentEvent, ...]:
        with self._lock:
            return tuple(self._events)

    @property
    def peak_concurrency(self) -> int:
        with self._lock:
            return self._peak_concurrency

    def cancel(self) -> None:
        self._cancel.set()

    def run_many(self, specs: Sequence[SubAgentSpec]) -> tuple[SubAgentResult, ...]:
        task_specs = tuple(specs)
        self._validate(task_specs)
        with ThreadPoolExecutor(max_workers=self.max_concurrency) as pool:
            futures = [pool.submit(self._run_one, spec) for spec in task_specs]
            return tuple(future.result() for future in futures)

    @staticmethod
    def summarize(results: Sequence[SubAgentResult]) -> SubAgentSummary:
        ordered = tuple(results)
        return SubAgentSummary(
            results=ordered,
            merged_output="\n".join(
                result.output for result in ordered if result.output is not None
            ),
            failed_task_ids=tuple(
                result.task_id
                for result in ordered
                if result.state in {SubAgentState.FAILED, SubAgentState.CANCELLED}
            ),
        )

    def _validate(self, specs: Sequence[SubAgentSpec]) -> None:
        task_ids = [spec.task_id for spec in specs]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("sub-agent task IDs must be unique")
        for spec in specs:
            if spec.depth > self.max_depth:
                raise SubAgentLimitError(
                    f"sub-agent depth {spec.depth} exceeds maximum {self.max_depth}"
                )
            if _permission_rank(spec.permission) > _permission_rank(self.parent_permission):
                raise PermissionError("child permission exceeds parent permission")

    def _run_one(self, spec: SubAgentSpec) -> SubAgentResult:
        self._record(spec.task_id, SubAgentState.RUNNING)
        with self._lock:
            self._active += 1
            self._peak_concurrency = max(self._peak_concurrency, self._active)
        child_budget = BudgetController(spec.budget or self.default_budget)
        parent_reserved = False
        try:
            if self._cancel.is_set():
                return self._finish(spec.task_id, SubAgentState.CANCELLED, error="cancelled")
            try:
                child_budget.check_round(
                    input_tokens=max(1, len(spec.prompt) // 4),
                    context_tokens=len(spec.prompt),
                )
                if self.parent_budget is not None:
                    self.parent_budget.start_round(
                        input_tokens=max(1, len(spec.prompt) // 4),
                        context_tokens=len(spec.prompt),
                    )
                    parent_reserved = True
            except BudgetExceeded as exc:
                return self._finish(spec.task_id, SubAgentState.FAILED, error=str(exc))
            task = SubAgentInput(spec, spec.context, child_budget, self._cancel)
            output = self.executor(task)
            if self._cancel.is_set():
                return self._finish(spec.task_id, SubAgentState.CANCELLED, error="cancelled")
            if not isinstance(output, str):
                raise TypeError("sub-agent executor must return text")
            return self._finish(spec.task_id, SubAgentState.COMPLETED, output=output)
        except Exception as exc:
            return self._finish(spec.task_id, SubAgentState.FAILED, error=str(exc))
        finally:
            if parent_reserved and self.parent_budget is not None:
                self.parent_budget.finish_round()
            child_budget.finish_round()
            with self._lock:
                self._active -= 1

    def _record(self, task_id: str, state: SubAgentState) -> None:
        with self._lock:
            self._events.append(SubAgentEvent(len(self._events), task_id, state))

    def _finish(
        self,
        task_id: str,
        state: SubAgentState,
        *,
        output: str | None = None,
        error: str | None = None,
    ) -> SubAgentResult:
        self._record(task_id, state)
        return SubAgentResult(task_id, state, output, error)


def _permission_rank(mode: PermissionMode) -> int:
    return {
        PermissionMode.PLAN: 0,
        PermissionMode.EDIT: 1,
        PermissionMode.HIGH: 2,
    }[mode]
