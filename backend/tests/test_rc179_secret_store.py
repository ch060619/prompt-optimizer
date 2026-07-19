from __future__ import annotations

import json

import pytest

from prompt_optimizer.config.service import ConfigService
from prompt_optimizer.secrets import (
    MemorySecretStore,
    SecretStoreUnavailableError,
    UnavailableSecretStore,
    create_secret_store,
    new_secret_reference,
)


def test_memory_secret_store_round_trip_and_reference_validation() -> None:
    store = MemorySecretStore()
    reference = new_secret_reference()

    store.put(reference, "test-secret")
    assert store.get(reference) == "test-secret"
    store.delete(reference)
    assert store.get(reference) is None

    with pytest.raises(ValueError):
        store.put("api-key-in-plain-text", "test-secret")


def test_config_service_persists_only_reference_and_resolves_secret(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    store = MemorySecretStore()
    service = ConfigService(user_path=config_path, secret_store=store)

    reference = service.set_user_secret("api_key", "provider-secret")

    raw = config_path.read_text(encoding="utf-8")
    assert "provider-secret" not in raw
    assert json.loads(raw)["api_key"] == reference
    assert service.resolve().values()["api_key"] == "provider-secret"
    assert service.resolve().display()["api_key"]["value"] == "secret://config/api_key"

    assert service.delete_user_secret("api_key") is True
    assert service.resolve().values()["api_key"] is None
    assert store.get(reference) is None


def test_plaintext_user_secret_is_rejected_but_session_secret_is_transient(tmp_path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"api_key": "plain-secret"}), encoding="utf-8")
    service = ConfigService(user_path=config_path, secret_store=MemorySecretStore())

    with pytest.raises(ValueError, match="opaque"):
        service.resolve()

    transient_service = ConfigService(
        user_path=tmp_path / "transient.json",
        secret_store=MemorySecretStore(),
    )
    snapshot = transient_service.resolve(session={"api_key": "temporary-secret"})
    assert snapshot.values()["api_key"] == "temporary-secret"
    assert not (tmp_path / "transient.json").exists()


def test_unavailable_store_fails_closed_for_persisted_secret(tmp_path) -> None:
    service = ConfigService(
        user_path=tmp_path / "config.json",
        secret_store=UnavailableSecretStore(),
    )

    with pytest.raises(SecretStoreUnavailableError):
        service.set_user_secret("api_key", "provider-secret")
    assert not (tmp_path / "config.json").exists()


def test_host_secret_store_round_trip_when_platform_backend_is_available() -> None:
    store = create_secret_store()
    if isinstance(store, UnavailableSecretStore):
        pytest.skip("host SecretStore backend is not installed")

    reference = new_secret_reference()
    try:
        store.put(reference, "temporary-platform-secret")
        assert store.get(reference) == "temporary-platform-secret"
    finally:
        store.delete(reference)
    assert store.get(reference) is None
