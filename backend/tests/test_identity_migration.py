from __future__ import annotations

from pathlib import Path

import pytest

from prompt_optimizer.identity import compatible_env
from prompt_optimizer.paths import app_data_dir, default_db_path

# RC ID: RC-054. Verify Rabbit Code identity migration and legacy Prompt Optimizer discovery.


def _clear_identity_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "RABBIT_CODE_HOME",
        "RABBIT_CODE_DB",
        "PROMPT_OPTIMIZER_HOME",
        "PROMPT_OPTIMIZER_DB",
    ):
        monkeypatch.delenv(name, raising=False)


def test_new_environment_names_take_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RABBIT_CODE_OPENAI_API_KEY", "new-key")
    monkeypatch.setenv("PROMPT_OPTIMIZER_OPENAI_API_KEY", "legacy-key")

    assert compatible_env("OPENAI_API_KEY") == "new-key"


def test_legacy_environment_names_warn_and_still_work(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("PROMPT_OPTIMIZER_HOME", str(tmp_path / "legacy-home"))

    with pytest.warns(DeprecationWarning, match="PROMPT_OPTIMIZER_HOME"):
        path = app_data_dir()

    assert path == tmp_path / "legacy-home"
    assert path.is_dir()


def test_existing_legacy_default_data_is_discovered(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    legacy_home = tmp_path / "prompt-optimizer"
    legacy_home.mkdir()

    with pytest.warns(DeprecationWarning, match="prompt-optimizer"):
        assert app_data_dir() == legacy_home
    assert default_db_path() == legacy_home / "prompt_optimizer.sqlite3"


def test_new_install_uses_rabbit_code_names(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("APPDATA", str(tmp_path))

    assert app_data_dir() == tmp_path / "rabbit-code"
    assert default_db_path() == tmp_path / "rabbit-code" / "rabbit-code.sqlite3"
