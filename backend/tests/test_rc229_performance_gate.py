from __future__ import annotations

from benchmarks.performance_gate import compare_reports


def _report(*, search_p95: float, memory_status: str = "blocked") -> dict[str, object]:
    return {
        "schema_version": "rc222-v1",
        "environment": {
            "commit": "abc1234",
            "machine": "test-machine",
            "processor": "test-cpu",
        },
        "measurements": {
            "search_query": {
                "status": "measured",
                "min_ms": search_p95 - 2,
                "p50_ms": search_p95 - 1,
                "p95_ms": search_p95,
                "max_ms": search_p95 + 1,
            },
            "memory": {"status": memory_status, "reason": "probe unavailable"},
        },
    }


def test_noise_threshold_accepts_small_variation_and_preserves_intervals() -> None:
    comparison = compare_reports(
        _report(search_p95=50),
        _report(search_p95=52),
        noise_ratio=0.05,
        noise_absolute=1,
    )

    assert comparison["status"] == "passed"
    assert comparison["regressions"] == []
    assert any(item["metric"] == "memory" for item in comparison["skipped"])
    assert comparison["metrics"]["search_query"]["baseline"]["p95_ms"] == 50
    assert comparison["metrics"]["search_query"]["current"]["max_ms"] == 53


def test_significant_regression_fails_with_actionable_statistics() -> None:
    comparison = compare_reports(
        _report(search_p95=50),
        _report(search_p95=70),
        noise_ratio=0.05,
        noise_absolute=1,
    )

    assert comparison["status"] == "failed"
    finding = comparison["regressions"][0]
    assert finding["metric"] == "search_query"
    assert finding["baseline_p95"] == 50
    assert finding["current_p95"] == 70
    assert finding["allowed_p95"] == 52.5
    assert finding["baseline_stats"]["min_ms"] == 48
    assert finding["current_stats"]["max_ms"] == 71


def test_unmeasured_current_metric_is_skipped_without_false_pass_or_failure() -> None:
    current = _report(search_p95=50)
    current["measurements"]["search_query"] = {
        "status": "blocked",
        "reason": "benchmark unavailable",
    }

    comparison = compare_reports(_report(search_p95=50), current)

    assert comparison["status"] == "passed"
    assert comparison["regressions"] == []
    assert any(
        item["metric"] == "search_query"
        and item["reason"] == "current measurement is blocked"
        for item in comparison["skipped"]
    )
