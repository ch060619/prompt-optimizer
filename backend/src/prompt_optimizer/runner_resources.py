from __future__ import annotations

from dataclasses import dataclass

from prompt_optimizer.hardware import HardwareReport

# RC ID: RC-196. Derive conservative runner resources from hardware capabilities.


@dataclass(frozen=True)
class RunnerResourceConfig:
    threads: int = 1
    gpu_layers: int = 0
    context_length: int = 4096
    concurrency: int = 1
    idle_timeout_seconds: float = 900.0
    temperature_limit_celsius: float = 90.0

    def __post_init__(self) -> None:
        if self.threads <= 0 or self.context_length <= 0 or self.concurrency <= 0:
            raise ValueError("runner resource counts must be positive")
        if (
            self.gpu_layers < 0
            or self.idle_timeout_seconds < 0
            or self.temperature_limit_celsius <= 0
        ):
            raise ValueError("runner resource limits must not be negative")

    def reduced_for_oom(self) -> RunnerResourceConfig:
        return RunnerResourceConfig(
            threads=max(1, self.threads - 1),
            gpu_layers=max(0, self.gpu_layers // 2),
            context_length=max(1024, int(self.context_length * 0.75)),
            concurrency=1,
            idle_timeout_seconds=self.idle_timeout_seconds,
            temperature_limit_celsius=self.temperature_limit_celsius,
        )

    def to_dict(self) -> dict[str, int | float]:
        return {
            "threads": self.threads,
            "gpu_layers": self.gpu_layers,
            "context_length": self.context_length,
            "concurrency": self.concurrency,
            "idle_timeout_seconds": self.idle_timeout_seconds,
            "temperature_limit_celsius": self.temperature_limit_celsius,
        }


def safe_runner_config(
    report: HardwareReport,
    *,
    context_length: int,
) -> RunnerResourceConfig:
    if context_length <= 0:
        raise ValueError("context_length must be positive")
    cpu = _mapping_value(report, "cpu")
    ram = _mapping_value(report, "ram")
    gpu = _mapping_value(report, "gpu")
    cores = _int_value(cpu.get("logical_cores"))
    total_ram = _int_value(ram.get("total_bytes"))
    devices = gpu.get("devices")
    gpu_devices = devices if isinstance(devices, list) else []
    gpu_memories = [
        memory
        for device in gpu_devices
        if isinstance(device, dict)
        for memory in [_int_value(device.get("memory_mb"))]
        if memory is not None
    ]
    gpu_memory = max(gpu_memories, default=0)
    threads = max(1, min(8, (cores - 1) if cores and cores > 1 else 1))
    effective_context = min(
        context_length,
        4096 if total_ram is not None and total_ram < 8 * 1024**3 else context_length,
    )
    gpu_layers = 16 if gpu_memory >= 4096 else 0
    if total_ram is not None and total_ram <= 4 * 1024**3:
        threads = 1
        effective_context = min(effective_context, 2048)
        gpu_layers = min(gpu_layers, 4)
    return RunnerResourceConfig(
        threads=threads,
        gpu_layers=gpu_layers,
        context_length=effective_context,
        concurrency=1,
    )


def _mapping_value(report: HardwareReport, name: str) -> dict[str, object]:
    field = report.fields.get(name)
    return field.value if field is not None and isinstance(field.value, dict) else {}


def _int_value(value: object) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None
