from __future__ import annotations

from dataclasses import dataclass

# RC ID: RC-224. Keep data ceilings explicit and shared across surfaces.


@dataclass(frozen=True)
class DataLimitDefaults:
    tool_output_bytes: int = 1_000_000
    max_tool_output_bytes: int = 10_000_000
    context_bytes: int = 32_000
    max_context_bytes: int = 1_000_000
    log_bytes: int = 10_000_000
    max_log_bytes: int = 100_000_000
    diff_bytes: int = 256_000
    max_diff_bytes: int = 5_000_000
    attachment_bytes: int = 10_000_000
    max_attachment_bytes: int = 100_000_000


DEFAULT_DATA_LIMITS = DataLimitDefaults()


def validate_limit(value: int, *, name: str, maximum: int) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    if value > maximum:
        raise ValueError(f"{name} exceeds the maximum of {maximum} bytes")
    return value
