from __future__ import annotations

import pytest
from backend.rabbit_code.file_tools import FileTools
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.sensitive_files import (
    SecretDetected,
    SecretScanner,
    SensitiveFilePolicy,
)

# RC ID: RC-206. Verify sensitive path gates, custom rules, and secret scanning.


def test_default_sensitive_paths_require_read_and_send_approval(tmp_path) -> None:
    policy = SensitiveFilePolicy(tmp_path)
    env_path = tmp_path / ".env"
    ssh_path = tmp_path / ".ssh" / "id_ed25519"
    send_paths = (env_path, tmp_path / "notes.txt")

    read = policy.authorize_read(env_path)
    send = policy.authorize_send(send_paths, target="openai")
    assert not read.allowed and read.requires_approval
    assert not send.allowed and send.requires_approval
    assert policy.authorize_read(env_path, approved=True).allowed
    assert policy.authorize_send(send_paths, target="openai", approved=True).allowed
    assert policy.classify(ssh_path).sensitive


def test_custom_sensitive_rule_is_visible_and_blocks_file_indexing(tmp_path) -> None:
    policy = SensitiveFilePolicy(tmp_path)
    policy.add_filename("customer-notes.md", category="user rule")
    target = tmp_path / "customer-notes.md"
    target.write_text("private", encoding="utf-8")
    tools = FileTools(tmp_path, sensitive_policy=policy)

    with pytest.raises(PermissionError, match="sensitive"):
        tools.read(target)
    assert target.relative_to(tmp_path) not in {entry.path for entry in tools.list()}
    assert tools.search("private") == ()
    assert tools.read(target, approval=True) == "private"


def test_secret_scanner_reports_only_metadata_and_blocks_export() -> None:
    scanner = SecretScanner()
    report = scanner.scan_text(
        "token = sk-test-1234567890abcdef\n"
        "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----\n"
    )

    assert not report.clean
    assert {finding.kind for finding in report.findings} >= {"api_key", "private_key"}
    assert all(not hasattr(finding, "value") for finding in report.findings)
    with pytest.raises(SecretDetected):
        scanner.assert_clean("password = 'long-secret-value'")


def test_sensitive_read_gate_is_independent_of_general_permission_mode(tmp_path) -> None:
    permission = PermissionPolicy(tmp_path)
    permission.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)
    sensitive = SensitiveFilePolicy(tmp_path)
    target = tmp_path / ".env.local"
    target.write_text("API_KEY=not-for-output", encoding="utf-8")
    tools = FileTools(tmp_path, permission_policy=permission, sensitive_policy=sensitive)

    with pytest.raises(PermissionError, match="sensitive"):
        tools.read(target)
    assert tools.read(target, approval=True).startswith("API_KEY=")
