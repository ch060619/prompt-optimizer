from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from prompt_optimizer.install_policy import (
    InstallPermissionError,
    ensure_user_install_paths,
    explicit_elevation_request,
    user_install_paths,
)

# RC ID: RC-199. Verify local-user installation paths and explicit elevation boundaries.


def test_user_install_paths_use_user_data_and_user_bin_without_admin(tmp_path) -> None:
    env = {
        "RABBIT_CODE_HOME": str(tmp_path / "rabbit-data"),
        "PATH": os.pathsep.join((str(tmp_path / "user-bin"), "system-path")),
    }

    paths = user_install_paths(environment=env, home=tmp_path / "home", windows=False)

    assert paths.data_dir == (tmp_path / "rabbit-data").resolve()
    assert paths.model_root == (tmp_path / "rabbit-data" / "local-models").resolve()
    assert paths.user_bin == (tmp_path / "home" / ".local" / "bin").resolve()
    assert paths.uses_admin is False
    assert paths.user_bin_in_path is False


def test_user_install_paths_can_be_created_and_reported_as_user_writable(tmp_path) -> None:
    paths = user_install_paths(environment={}, home=tmp_path / "home", windows=True)

    report = ensure_user_install_paths(paths)

    assert report.writable is True
    assert report.model_root.exists()
    assert report.user_bin.exists()
    assert report.elevation_required is False


def test_elevation_requires_explicit_confirmation_and_has_manual_alternative() -> None:
    request = explicit_elevation_request(
        command="install runner",
        reason="the selected system directory is not writable",
        alternative="choose a user model directory or install the runner manually",
    )

    assert request.confirmed is False
    assert request.to_dict()["alternative"] == (
        "choose a user model directory or install the runner manually"
    )
    with pytest.raises(InstallPermissionError, match="explicit confirmation"):
        request.require_confirmation()
    confirmed = request.with_confirmation(True)
    assert confirmed.confirmed is True


def test_system_directory_is_rejected_without_mutating_it(tmp_path) -> None:
    system_like = tmp_path / "system"
    system_like.mkdir()
    system_like.chmod(0o555)
    try:
        paths = user_install_paths(environment={}, home=tmp_path / "home", windows=False)
        paths = paths.with_model_root(system_like / "models")
        with pytest.raises(InstallPermissionError, match="writable"):
            ensure_user_install_paths(paths)
        assert not (system_like / "models").exists()
    finally:
        system_like.chmod(0o755)


def test_cli_defaults_to_user_model_root_without_root_argument(tmp_path) -> None:
    repository = Path(__file__).parents[2]
    environment = os.environ.copy()
    environment["RABBIT_CODE_HOME"] = str(tmp_path / "rabbit-home")
    environment["PYTHONPATH"] = os.pathsep.join(
        (
            str(repository / "backend" / "src"),
            str(repository / "backend"),
            str(repository / "packages" / "protocol"),
        )
    )

    result = subprocess.run(
        [sys.executable, "scripts/local_model_install.py", "status"],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    assert '"state": null' in result.stdout
    assert (tmp_path / "rabbit-home" / "local-models").is_dir()


def test_platform_wrappers_do_not_request_elevation() -> None:
    repository = Path(__file__).parents[2]
    powershell = (repository / "scripts" / "install-local-model.ps1").read_text(encoding="utf-8")
    shell = (repository / "scripts" / "install-local-model.sh").read_text(encoding="utf-8")

    assert "RunAs" not in powershell
    assert "sudo " not in shell
