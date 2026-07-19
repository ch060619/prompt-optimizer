from __future__ import annotations

import time
from dataclasses import dataclass, replace
from threading import Lock

# RC ID: RC-072. Enforce atomic Agent round, token, cost, context, wall-clock, and concurrency.


@dataclass(frozen=True)
class BudgetLimits:
    max_rounds: int | None = None
    max_wall_clock_seconds: float | None = None
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_cost: float | None = None
    max_context_tokens: int | None = None
    max_concurrency: int | None = None
    warning_ratio: float = 0.8

    def __post_init__(self) -> None:
        for name in (
            "max_rounds",
            "max_input_tokens",
            "max_output_tokens",
            "max_context_tokens",
            "max_concurrency",
        ):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.max_wall_clock_seconds is not None and self.max_wall_clock_seconds < 0:
            raise ValueError("max_wall_clock_seconds must be non-negative")
        if self.max_cost is not None and self.max_cost < 0:
            raise ValueError("max_cost must be non-negative")
        if not 0 < self.warning_ratio <= 1:
            raise ValueError("warning_ratio must be in (0, 1]")


@dataclass(frozen=True)
class BudgetUsage:
    rounds: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    context_tokens: int = 0
    active_concurrency: int = 0


@dataclass(frozen=True)
class BudgetNotice:
    dimension: str
    used: float
    limit: float
    message: str


class BudgetExceeded(RuntimeError):
    def __init__(self, dimension: str, used: float, limit: float) -> None:
        self.dimension = dimension
        self.used = used
        self.limit = limit
        super().__init__(f"budget exceeded for {dimension}: used {used}, limit {limit}")


class BudgetController:
    def __init__(self, limits: BudgetLimits) -> None:
        self.limits = limits
        self._usage = BudgetUsage()
        self._started_at = time.monotonic()
        self._lock = Lock()

    @property
    def usage(self) -> BudgetUsage:
        with self._lock:
            return self._usage

    def start_round(
        self,
        *,
        input_tokens: int,
        context_tokens: int = 0,
    ) -> tuple[BudgetNotice, ...]:
        if input_tokens < 0 or context_tokens < 0:
            raise ValueError("token usage must be non-negative")
        with self._lock:
            self._check_wall_clock_locked()
            next_usage = replace(
                self._usage,
                rounds=self._usage.rounds + 1,
                input_tokens=self._usage.input_tokens + input_tokens,
                context_tokens=max(self._usage.context_tokens, context_tokens),
                active_concurrency=self._usage.active_concurrency + 1,
            )
            self._check_limits_locked(next_usage)
            self._usage = next_usage
            return self._warnings_locked(next_usage)

    def check_round(
        self,
        *,
        input_tokens: int,
        context_tokens: int = 0,
    ) -> None:
        """Validate a potential round without reserving it for a child executor."""
        if input_tokens < 0 or context_tokens < 0:
            raise ValueError("token usage must be non-negative")
        with self._lock:
            self._check_wall_clock_locked()
            next_usage = replace(
                self._usage,
                rounds=self._usage.rounds + 1,
                input_tokens=self._usage.input_tokens + input_tokens,
                context_tokens=max(self._usage.context_tokens, context_tokens),
                active_concurrency=self._usage.active_concurrency + 1,
            )
            self._check_limits_locked(next_usage)

    def record_output(
        self,
        *,
        output_tokens: int,
        cost: float = 0.0,
    ) -> tuple[BudgetNotice, ...]:
        if output_tokens < 0 or cost < 0:
            raise ValueError("output usage must be non-negative")
        with self._lock:
            self._check_wall_clock_locked()
            next_usage = replace(
                self._usage,
                output_tokens=self._usage.output_tokens + output_tokens,
                cost=self._usage.cost + cost,
            )
            self._check_limits_locked(next_usage)
            self._usage = next_usage
            return self._warnings_locked(next_usage)

    def finish_round(self) -> None:
        with self._lock:
            self._usage = replace(
                self._usage,
                active_concurrency=max(0, self._usage.active_concurrency - 1),
            )

    def check_wall_clock(self) -> None:
        with self._lock:
            self._check_wall_clock_locked()

    def _check_wall_clock_locked(self) -> None:
        limit = self.limits.max_wall_clock_seconds
        if limit is not None and time.monotonic() - self._started_at > limit:
            raise BudgetExceeded("wall_clock_seconds", time.monotonic() - self._started_at, limit)

    def _check_limits_locked(self, usage: BudgetUsage) -> None:
        dimensions = (
            ("rounds", usage.rounds, self.limits.max_rounds),
            ("input_tokens", usage.input_tokens, self.limits.max_input_tokens),
            ("output_tokens", usage.output_tokens, self.limits.max_output_tokens),
            ("cost", usage.cost, self.limits.max_cost),
            ("context_tokens", usage.context_tokens, self.limits.max_context_tokens),
            ("concurrency", usage.active_concurrency, self.limits.max_concurrency),
        )
        for dimension, used, limit in dimensions:
            if limit is not None and used > limit:
                raise BudgetExceeded(dimension, used, limit)

    def _warnings_locked(self, usage: BudgetUsage) -> tuple[BudgetNotice, ...]:
        dimensions = (
            ("rounds", usage.rounds, self.limits.max_rounds),
            ("input_tokens", usage.input_tokens, self.limits.max_input_tokens),
            ("output_tokens", usage.output_tokens, self.limits.max_output_tokens),
            ("cost", usage.cost, self.limits.max_cost),
            ("context_tokens", usage.context_tokens, self.limits.max_context_tokens),
            ("concurrency", usage.active_concurrency, self.limits.max_concurrency),
        )
        notices = []
        for dimension, used, limit in dimensions:
            if limit is not None and used >= limit * self.limits.warning_ratio:
                notices.append(
                    BudgetNotice(
                        dimension,
                        float(used),
                        float(limit),
                        f"budget warning: {dimension} used {used} of {limit}",
                    )
                )
        return tuple(notices)
