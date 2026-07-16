from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from pytest import MonkeyPatch

from prompt_optimizer.auth.service import AuthService
from prompt_optimizer.core.models import UserPublic
from prompt_optimizer.providers.registry import ProviderRegistry
from prompt_optimizer.storage.service import StorageService

# RC ID: RC-052. Keep local identity, password records, and Provider credentials separate.


def test_jwt_contains_local_identity_only() -> None:
    service = AuthService(secret="rc-052-test-secret")
    user = UserPublic(id=7, username="local-user", created_at=datetime.now(UTC))

    payload = service._decode(service.create_token(user).split(".")[1])

    assert set(payload) == {"sub", "username", "exp"}
    assert "api_key" not in payload
    assert "provider" not in payload


def test_provider_credentials_are_runtime_config_and_not_user_storage(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROMPT_OPTIMIZER_OPENAI_API_KEY", "runtime-only-key")
    config = ProviderRegistry._config_from_env("openai")

    storage = StorageService(tmp_path / "auth-boundary.sqlite3")
    storage.create_user("local-user", AuthService().hash_password("secret123"))
    with sqlite3.connect(storage.db_path) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(users)")]
        rows = connection.execute(
            "SELECT * FROM users WHERE username = ?", ("local-user",)
        ).fetchall()

    assert config.api_key == "runtime-only-key"
    assert columns == ["id", "username", "password_hash", "created_at"]
    assert len(rows) == 1
    assert "runtime-only-key" not in repr(rows[0])
