from __future__ import annotations

import sys
from pathlib import Path

import pytest
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.process_tools import ProcessManager
from backend.rabbit_code.sandbox import (
    SandboxApprovalRequired,
    SandboxController,
    SandboxGuarantee,
    SandboxUnavailable,
    detect_sandbox,
)

# RC ID: RC-204. Verify platform capability detection, reduced fallback, and boundaries.


def test_windows_report_records_job_object_and_non_equivalent_controls() -> None:
    report = detect_sandbox(platform_name="Windows", executable_finder=lambda _name: None)

    assert report.platform == "windows"
    assert report.capability("job_object").available
    assert not report.capability("appcontainer").available
    assert not report.capability("acl_workspace").available
    assert "AppContainer" in report.limitations[0]


def test_linux_bwrap_report_builds_workspace_and_network_isolation(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.rabbit_code.sandbox.platform.system",
        lambda: "Linux",
    )
    monkeypatch.setattr(
        "backend.rabbit_code.sandbox.shutil.which",
        lambda name: "/usr/bin/bwrap" if name == "bwrap" else None,
    )
    report = detect_sandbox(
        executable_finder=lambda name: "/usr/bin/bwrap" if name == "bwrap" else None
    )
    controller = SandboxController(Path.cwd(), report=report)

    spec = controller.prepare(("python", "-c", "print('ok')"), cwd=".")

    assert spec.guarantee is SandboxGuarantee.BWRAP
    assert spec.command[0] == "/usr/bin/bwrap"
    assert "--unshare-net" in spec.command
    assert "--ro-bind" in spec.command


def test_unavailable_strong_sandbox_requires_approval_before_reduced_launch(tmp_path) -> None:
    report = detect_sandbox(platform_name="Linux", executable_finder=lambda _name: None)
    controller = SandboxController(tmp_path, report=report)

    with pytest.raises(SandboxApprovalRequired):
        controller.prepare(("python", "-c", "pass"), cwd=".")
    reduced = controller.prepare(("python", "-c", "pass"), cwd=".", approval=True)
    assert reduced.guarantee is SandboxGuarantee.REDUCED
    assert reduced.requires_approval

    with pytest.raises(SandboxUnavailable):
        SandboxController(tmp_path, report=report, require_strong=True).prepare(
            ("python", "-c", "pass"), cwd="."
        )


def test_path_escape_and_symlink_escape_are_rejected(tmp_path) -> None:
    controller = SandboxController(tmp_path, report=detect_sandbox(platform_name="Other"))

    with pytest.raises(PermissionError, match="workspace"):
        controller.prepare(("python", "-c", "pass"), cwd=tmp_path.parent)

    outside = tmp_path.parent / "outside"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(PermissionError, match="symlink"):
        controller.prepare(("python", "-c", "pass"), cwd=link)


def test_process_manager_launches_reduced_sandbox_only_after_approval(tmp_path) -> None:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    controller = SandboxController(
        tmp_path,
        report=detect_sandbox(platform_name="Other"),
    )
    with ProcessManager(tmp_path, permission_policy=policy, sandbox=controller) as manager:
        record = manager.start((sys.executable, "-c", "print('approved')"), approval=True)
        finished = manager.wait(record.process_id, timeout_seconds=5)
        assert finished.returncode == 0
