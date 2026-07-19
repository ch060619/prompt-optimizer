from __future__ import annotations

import json
from pathlib import Path

import pytest
from backend.rabbit_code.maintenance import (
    CompletionShell,
    build_doctor_report,
    build_uninstall_plan,
    execute_uninstall,
    installation_paths,
    package_version,
    render_completion,
)
from typer.testing import CliRunner

from prompt_optimizer.cli.app import app

# RC ID: RC-108. Verify completion, installation/version diagnostics, doctor, and safe cleanup.


@pytest.mark.parametrize(
    "shell,marker",
    (
        (CompletionShell.BASH, "complete -F _rabbit_completion rabbit"),
        (CompletionShell.ZSH, "compdef _rabbit rabbit"),
        (CompletionShell.FISH, "complete -c rabbit"),
        (CompletionShell.POWERSHELL, "Register-ArgumentCompleter"),
    ),
)
def test_supported_shell_completions_are_loadable_scripts(
    shell: CompletionShell,
    marker: str,
) -> None:
    script = render_completion(shell)
    assert marker in script
    assert "doctor" in script
    assert "uninstall" in script


def test_installation_paths_and_version_are_explicit() -> None:
    paths = installation_paths()
    assert paths.package_root.is_dir()
    assert paths.data_dir.is_absolute()
    assert paths.database_path.parent == paths.data_dir
    assert package_version() == "3.0.0"


def test_doctor_report_has_stable_checks_and_no_secret_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "rabbit-code"
    monkeypatch.setenv("RABBIT_CODE_HOME", str(data_dir))
    report = build_doctor_report()

    payload = report.to_dict()
    assert payload["version"] == "3.0.0"
    assert {check["name"] for check in payload["checks"]} >= {
        "python",
        "package",
        "executable",
        "data_dir",
        "database",
    }
    assert "api_key" not in json.dumps(payload, ensure_ascii=False)


def test_uninstall_preserves_database_by_default_and_never_touches_project(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "rabbit-code"
    cache = data_dir / "cache"
    cache.mkdir(parents=True)
    (cache / "temporary.bin").write_bytes(b"cache")
    database = data_dir / "rabbit-code.sqlite3"
    database.write_bytes(b"database")
    project = tmp_path / "project"
    project.mkdir()
    (project / "source.py").write_text("print('keep')", encoding="utf-8")

    plan = build_uninstall_plan(data_dir=data_dir)
    execute_uninstall(plan, confirmed=True)
    assert not cache.exists()
    assert database.exists()
    assert (project / "source.py").exists()

    with pytest.raises(PermissionError, match="confirmation"):
        execute_uninstall(build_uninstall_plan(data_dir=data_dir), purge_data=True)

    execute_uninstall(
        build_uninstall_plan(data_dir=data_dir),
        purge_data=True,
        confirmed=True,
    )
    assert not data_dir.exists()
    assert (project / "source.py").exists()


def test_uninstall_rejects_workspace_like_or_unknown_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Rabbit Code data directory"):
        build_uninstall_plan(data_dir=tmp_path / "project")


def test_cli_exposes_version_path_doctor_completion_and_dry_run_uninstall(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RABBIT_CODE_HOME", str(tmp_path / "rabbit-code"))
    runner = CliRunner()

    version = runner.invoke(app, ["version"])
    assert version.exit_code == 0
    assert "Rabbit Code 3.0.0" in version.stdout

    paths = runner.invoke(app, ["path", "--json"])
    assert paths.exit_code == 0
    assert json.loads(paths.stdout)["data_dir"].endswith("rabbit-code")

    doctor = runner.invoke(app, ["doctor", "--json"])
    assert doctor.exit_code == 0
    assert json.loads(doctor.stdout)["version"] == "3.0.0"

    completion = runner.invoke(app, ["completion", "bash"])
    assert completion.exit_code == 0
    assert "complete -F _rabbit_completion rabbit" in completion.stdout

    uninstall = runner.invoke(app, ["uninstall", "--purge-data"])
    assert uninstall.exit_code == 0
    assert "dry-run" in uninstall.stdout
