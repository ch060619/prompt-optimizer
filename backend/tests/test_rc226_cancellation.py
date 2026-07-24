from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Any

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.providers.base import (
    ModelRequest,
    ModelResponse,
    ProviderCancelledError,
    ProviderCapabilities,
    ProviderEvent,
)
from prompt_optimizer.providers.registry import ProviderRegistry
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-226. Verify cancellation IDs reach providers and prevent persistence.


class BlockingProvider:
    name = "offline"
    display_name = "Blocking test provider"
    model = None
    network_access = False
    execution_location = "local"
    credential_ref = None
    capabilities = ProviderCapabilities(streaming=True)

    def __init__(self) -> None:
        self.started = Event()

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self.started.set()
        while request.cancel_event is None or not request.cancel_event.is_set():
            sleep(0.01)
        raise ProviderCancelledError("优化请求已取消。")

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        yield ProviderEvent("started")


def test_cancel_id_reaches_provider_and_does_not_save_history(tmp_path: Path) -> None:
    provider = BlockingProvider()
    storage = StorageService(tmp_path / "rc226.sqlite3")
    services = AppServices(
        versions=VersionService(storage),
        providers=ProviderRegistry(providers={"offline": provider}),
    )
    result: list[Any] = []

    def run() -> None:
        try:
            services.optimization.optimize(
                original_prompt="cancel this",
                prompt="cancel this",
                template=None,
                request_id="rc226-request",
            )
        except BaseException as exc:
            result.append(exc)

    worker = Thread(target=run)
    worker.start()
    assert provider.started.wait(timeout=2)
    assert services.optimization.cancel("rc226-request")
    worker.join(timeout=2)

    assert result and isinstance(result[0], ProviderCancelledError)
    assert not worker.is_alive()
    assert storage.list_versions() == []
    assert not services.optimization.cancel("rc226-request")


def test_cancel_endpoint_is_versioned_and_idempotent() -> None:
    client = TestClient(create_app())
    assert "/api/v1/optimize/{request_id}/cancel" in client.app.openapi()["paths"]
    response = client.post("/api/v1/optimize/unknown-request/cancel")
    assert response.status_code == 200
    assert response.json() == {"request_id": "unknown-request", "cancelled": False}
