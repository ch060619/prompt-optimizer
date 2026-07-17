from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from prompt_optimizer.cli.app import app
from prompt_optimizer.config import ConfigService

# RC ID: RC-065. Verify layered configuration precedence, scopes, and safe display.


@pytest.mark.parametrize(
    ("layer", "expected_source"),
    [
        ("default", "default"),
        ("user", "user"),
        ("workspace", "workspace"),
        ("session", "session"),
        ("cli", "cli"),
    ],
)
def test_higher_layer_wins_for_provider(
    layer: str,
    expected_source: str,
    tmp_path: Path,
) -> None:
    user_path = tmp_path / "user.json"
    workspace_root = tmp_path / "workspace"
    workspace_path = workspace_root / ".rabbit-code" / "config.json"
    rank = {"default": 0, "user": 1, "workspace": 2, "session": 3, "cli": 4}
    if rank[layer] >= rank["user"]:
        user_path.write_text(json.dumps({"provider": "user"}), encoding="utf-8")
    if rank[layer] >= rank["workspace"]:
        workspace_path.parent.mkdir(parents=True)
        workspace_path.write_text(json.dumps({"provider": "workspace"}), encoding="utf-8")
    service = ConfigService(user_path=user_path, workspace_root=workspace_root)

    session = {"provider": "session"} if layer in {"session", "cli"} else None
    cli = {"provider": "cli"} if layer == "cli" else None
    snapshot = service.resolve(session=session, cli=cli)

    assert snapshot.source_of("provider") == expected_source
    expected_value = "offline" if layer == "default" else expected_source
    assert snapshot.values()["provider"] == expected_value


def test_config_fields_are_typed_scoped_and_secrets_are_not_displayed(tmp_path: Path) -> None:
    user_path = tmp_path / "user.json"
    user_path.write_text(
        json.dumps({"api_key": "runtime-secret", "timeout_seconds": 12.5}),
        encoding="utf-8",
    )
    service = ConfigService(user_path=user_path)
    snapshot = service.resolve(session={"timeout_seconds": 15.0})

    display = snapshot.display()
    assert snapshot.values()["api_key"] == "runtime-secret"
    assert display["api_key"]["value"] == "secret://config/api_key"
    assert "runtime-secret" not in json.dumps(display, ensure_ascii=False)
    assert display["timeout_seconds"]["source"] == "session"
    assert display["timeout_seconds"]["scope"] == "runtime"

    with pytest.raises(ValueError, match="api_key.*session"):
        service.resolve(session={"api_key": "not-allowed"})
    with pytest.raises(ValueError, match="整数"):
        service.resolve(cli={"max_retries": True})
    with pytest.raises(ValueError, match="未知配置项"):
        service.resolve(cli={"unknown": "value"})


def test_config_cli_shows_sources_without_secret_values(tmp_path: Path) -> None:
    user_path = tmp_path / "user.json"
    user_path.write_text(json.dumps({"api_key": "secret-from-file"}), encoding="utf-8")
    workspace_root = tmp_path / "workspace"
    workspace_path = workspace_root / ".rabbit-code" / "config.json"
    workspace_path.parent.mkdir(parents=True)
    workspace_path.write_text(json.dumps({"provider": "openai"}), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "config",
            "show",
            "--user-config",
            str(user_path),
            "--workspace",
            str(workspace_root),
            "--session",
            "timeout_seconds=15",
            "--override",
            "max_retries=4",
        ],
    )

    assert result.exit_code == 0
    assert "openai" in result.stdout
    assert "session" in result.stdout
    assert "cli" in result.stdout
    assert "secret-from-file" not in result.stdout
    assert "secret://config/api_key" in result.stdout
