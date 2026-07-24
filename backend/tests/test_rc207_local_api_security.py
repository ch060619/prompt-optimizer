from __future__ import annotations

from pathlib import Path

from backend.rabbit_code.sidecar import generate_startup_token
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app_server
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-207. Verify strict loopback, Host/Origin, token, and body boundaries.


def _client(tmp_path: Path) -> TestClient:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc207.sqlite3"))
    services.export = ExportService()
    app = create_app_server(
        services,
        startup_token=generate_startup_token(),
        strict_boundary=True,
        max_body_bytes=128,
    )
    return TestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000))


def test_startup_token_is_high_entropy_and_strict_health_is_loopback_only(tmp_path: Path) -> None:
    token = generate_startup_token()
    assert len(token) >= 40
    with _client(tmp_path) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.headers["X-Rabbit-Code-Protocol"] == "v1"


def test_strict_boundary_rejects_bad_host_origin_token_and_body(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        base_headers = {
            "X-Rabbit-Code-Startup-Token": "not-the-token",
            "X-Rabbit-Code-Protocol": "v1",
        }
        assert (
            client.post("/api/v1/analyze", json={"prompt": "x"}, headers=base_headers).status_code
            == 401
        )
        token = client.app.state.startup_token
        assert client.post(
            "/api/v1/analyze",
            json={"prompt": "x"},
            headers={
                **base_headers,
                "Host": "evil.example",
                "X-Rabbit-Code-Startup-Token": token,
            },
        ).status_code == 400
        assert client.post(
            "/api/v1/analyze",
            json={"prompt": "x"},
            headers={
                **base_headers,
                "Origin": "https://evil.example",
                "X-Rabbit-Code-Startup-Token": token,
            },
        ).status_code == 403
        oversized = {"prompt": "x" * 200}
        assert client.post(
            "/api/v1/analyze",
            json=oversized,
            headers={
                "X-Rabbit-Code-Startup-Token": token,
                "X-Rabbit-Code-Protocol": "v1",
            },
        ).status_code == 413


def test_strict_boundary_limits_chunked_body_without_content_length(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        token = client.app.state.startup_token

        def chunks():
            yield b'{"prompt":"'
            yield b"x" * 200
            yield b'"}'

        response = client.post(
            "/api/v1/analyze",
            content=chunks(),
            headers={
                "Content-Type": "application/json",
                "X-Rabbit-Code-Startup-Token": token,
                "X-Rabbit-Code-Protocol": "v1",
            },
        )

    assert response.status_code == 413, response.text
