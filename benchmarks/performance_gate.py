from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping, Sequence


METRICS: tuple[tuple[str, str], ...] = (
    ("cli_first_response", "p95_ms"),
    ("offline_first_token", "p95_ms"),
    ("search_query", "p95_ms"),
    ("diff", "p95_ms"),
    ("frontend_dist", "bytes"),
    ("memory", "rss_bytes"),
    ("gui_cold_start", "p95_ms"),
    ("gui_hot_start", "p95_ms"),
    ("backend_package", "bytes"),
)
STAT_KEYS = ("min_ms", "p50_ms", "p95_ms", "max_ms", "bytes", "rss_bytes")


def compare_reports(
    baseline: Mapping[str, object],
    current: Mapping[str, object],
    *,
    noise_ratio: float = 0.10,
    noise_absolute: float = 1.0,
) -> dict[str, object]:
    """Compare only metrics measured in both reports using a bounded noise budget."""
    if noise_ratio < 0 or noise_absolute < 0:
        raise ValueError("noise thresholds must not be negative")
    baseline_measurements = _mapping(baseline.get("measurements"))
    current_measurements = _mapping(current.get("measurements"))
    metrics: dict[str, object] = {}
    skipped: list[dict[str, str]] = []
    regressions: list[dict[str, object]] = []
    for metric, value_key in METRICS:
        baseline_item = _mapping(baseline_measurements.get(metric))
        current_item = _mapping(current_measurements.get(metric))
        if baseline_item.get("status") != "measured":
            skipped.append({"metric": metric, "reason": "baseline measurement is blocked"})
            continue
        if current_item.get("status") != "measured":
            skipped.append({"metric": metric, "reason": "current measurement is blocked"})
            continue
        baseline_value = _number(baseline_item.get(value_key))
        current_value = _number(current_item.get(value_key))
        if baseline_value is None or current_value is None:
            skipped.append({"metric": metric, "reason": "measurement value is invalid"})
            continue
        allowed = max(baseline_value * (1 + noise_ratio), baseline_value + noise_absolute)
        metric_result = {
            "baseline": _stats(baseline_item),
            "current": _stats(current_item),
            "allowed_value": _round(allowed),
        }
        metrics[metric] = metric_result
        if current_value > allowed:
            regressions.append(
                {
                    "metric": metric,
                    "baseline_p95": _round(baseline_value),
                    "current_p95": _round(current_value),
                    "allowed_p95": _round(allowed),
                    "baseline_stats": _stats(baseline_item),
                    "current_stats": _stats(current_item),
                }
            )
    return {
        "schema_version": "rc229-v1",
        "status": "failed" if regressions else "passed",
        "noise_ratio": noise_ratio,
        "noise_absolute": noise_absolute,
        "baseline_environment": dict(_mapping(baseline.get("environment"))),
        "current_environment": dict(_mapping(current.get("environment"))),
        "metrics": metrics,
        "skipped": skipped,
        "regressions": regressions,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two Rabbit Code performance reports.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--comparison-output", type=Path)
    parser.add_argument("--noise-ratio", type=float, default=0.10)
    parser.add_argument("--noise-absolute", type=float, default=1.0)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    baseline = _load_report(args.baseline)
    current = _load_report(args.current)
    comparison = compare_reports(
        baseline,
        current,
        noise_ratio=args.noise_ratio,
        noise_absolute=args.noise_absolute,
    )
    serialized = json.dumps(comparison, ensure_ascii=False, indent=2) + "\n"
    if args.comparison_output is not None:
        args.comparison_output.parent.mkdir(parents=True, exist_ok=True)
        args.comparison_output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return int(args.check and comparison["status"] == "failed")


def _load_report(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"performance report must be an object: {path}")
    return payload


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _number(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _stats(measurement: Mapping[str, object]) -> dict[str, float | int]:
    return {
        key: value
        for key in STAT_KEYS
        if isinstance((value := measurement.get(key)), (int, float))
    }


def _round(value: float) -> float:
    return round(value, 6)


if __name__ == "__main__":
    raise SystemExit(main())
