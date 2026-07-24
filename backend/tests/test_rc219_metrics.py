from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.metrics import LocalMetricsAggregator
from prompt_optimizer.services import AppServices


def test_local_metrics_snapshot_aggregates_fixed_load_without_content() -> None:
    metrics = LocalMetricsAggregator()
    metrics.record_request(
        provider="offline",
        latency_ms=20,
        success=True,
        input_tokens=10,
        output_tokens=4,
    )
    metrics.record_request(provider="offline", latency_ms=30, success=False)
    metrics.record_first_token(12)
    metrics.record_tool(success=True)
    metrics.record_model_load(model="qwen/model", latency_ms=40, success=True)
    metrics.record_resources(cpu_percent=25, ram_bytes=100, gpu_memory_bytes=200)

    snapshot = metrics.snapshot()

    assert snapshot.schema_version == "rc219-v1"
    assert snapshot.requests_total == 2
    assert snapshot.requests_succeeded == 1
    assert snapshot.requests_failed == 1
    assert snapshot.failure_rate == 0.5
    assert snapshot.average_latency_ms == 25
    assert snapshot.average_first_token_ms == 12
    assert snapshot.input_tokens == 10
    assert snapshot.output_tokens == 4
    assert snapshot.tool_success_rate == 1
    assert snapshot.average_model_load_ms == 40
    assert snapshot.max_cpu_percent == 25
    assert snapshot.max_ram_bytes == 100
    assert snapshot.max_gpu_memory_bytes == 200
    assert "prompt" not in snapshot.model_dump_json().lower()


def test_metrics_reject_sensitive_labels_and_invalid_resource_values() -> None:
    metrics = LocalMetricsAggregator()

    with pytest.raises(ValueError):
        metrics.record_request(provider="api_key", latency_ms=1, success=True)
    with pytest.raises(ValueError):
        metrics.record_resources(cpu_percent=101)


def test_metrics_api_returns_versioned_local_report() -> None:
    services = AppServices()
    services.metrics.record_request(provider="offline", latency_ms=1, success=True)

    with TestClient(create_app(services)) as client:
        response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "rc219-v1"
    assert payload["requests_total"] == 1
    assert payload["provider_metrics"]["offline"]["requests_succeeded"] == 1


def test_optimization_service_records_request_metrics() -> None:
    services = AppServices()

    services.optimize_and_save(
        original_prompt="写一个摘要",
        prompt="写一个摘要",
        template=None,
        provider_name="offline",
        owner_id=None,
    )

    snapshot = services.metrics.snapshot()
    assert snapshot.requests_total == 1
    assert snapshot.requests_succeeded == 1
    assert snapshot.provider_metrics["offline"]["requests_succeeded"] == 1
