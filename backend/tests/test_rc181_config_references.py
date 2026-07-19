from __future__ import annotations

import json

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.config import ConfigService
from prompt_optimizer.secrets import MemorySecretStore, new_secret_reference
from prompt_optimizer.services import AppServices

# RC ID: RC-181. Verify environment/keychain references, precedence, and safe API display.


def test_environment_reference_is_resolved_again_on_each_snapshot(tmp_path) -> None:
    environment = {
        "PROVIDER_KEY": "first-secret",
        "RABBIT_CODE_PROVIDER": "env-provider",
        "RABBIT_CODE_TIMEOUT_SECONDS": "3.5",
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"api_key": "env:PROVIDER_KEY", "provider": "file-provider"}),
        encoding="utf-8",
    )
    service = ConfigService(
        user_path=config_path,
        secret_store=MemorySecretStore(),
        environment=environment,
    )

    first = service.resolve()
    assert first.values()["api_key"] == "first-secret"
    assert first.values()["provider"] == "env-provider"
    assert first.values()["timeout_seconds"] == 3.5
    assert first.source_of("provider") == "env"
    assert first.display()["api_key"]["source_kind"] == "environment"
    assert first.display()["api_key"]["value"] == "secret://config/api_key"
    assert "first-secret" not in json.dumps(first.display())

    environment["PROVIDER_KEY"] = "changed-secret"
    second = service.resolve()
    assert second.values()["api_key"] == "changed-secret"


def test_reference_priority_is_config_file_then_environment_then_session_and_cli(tmp_path) -> None:
    user_path = tmp_path / "user.json"
    user_path.write_text(json.dumps({"provider": "user-provider"}), encoding="utf-8")
    workspace = tmp_path / "workspace"
    (workspace / ".rabbit-code").mkdir(parents=True)
    (workspace / ".rabbit-code" / "config.json").write_text(
        json.dumps({"provider": "workspace-provider"}),
        encoding="utf-8",
    )
    service = ConfigService(
        user_path=user_path,
        workspace_root=workspace,
        secret_store=MemorySecretStore(),
        environment={"RABBIT_CODE_PROVIDER": "env-provider"},
    )

    resolved = service.resolve(
        session={"provider": "session-provider"},
        cli={"provider": "cli-provider"},
    )
    assert resolved.values()["provider"] == "cli-provider"
    assert resolved.source_of("provider") == "cli"
    assert (
        service.resolve(session={"provider": "session-provider"}).values()["provider"]
        == "session-provider"
    )
    assert service.resolve().values()["provider"] == "env-provider"


def test_keychain_reference_is_displayed_as_source_without_secret(tmp_path) -> None:
    store = MemorySecretStore()
    reference = new_secret_reference()
    store.put(reference, "keychain-secret")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"api_key": f"keychain:{reference}"}), encoding="utf-8")

    snapshot = ConfigService(user_path=config_path, secret_store=store, environment={}).resolve()

    assert snapshot.values()["api_key"] == "keychain-secret"
    assert snapshot.display()["api_key"]["source_label"] == "keychain"
    assert "keychain-secret" not in json.dumps(snapshot.display())


def test_config_api_returns_source_only_for_environment_secret(tmp_path) -> None:
    secret = "api-secret-from-environment"
    config = ConfigService(
        user_path=tmp_path / "config.json",
        secret_store=MemorySecretStore(),
        environment={"RABBIT_CODE_API_KEY": secret},
    )
    client = TestClient(create_app(AppServices(config=config)))

    response = client.get("/api/v1/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_key"]["source_label"] == "environment variable"
    assert payload["api_key"]["value"] == "secret://config/api_key"
    assert secret not in response.text
