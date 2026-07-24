from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from prompt_optimizer.audit import AuditCategory, AuditLogService

# RC ID: RC-212. Verify minimal audit metadata, chain integrity, retention, and deletion.


def test_audit_records_key_decisions_without_sensitive_metadata(tmp_path: Path) -> None:
    service = AuditLogService(tmp_path / "audit.sqlite3")

    event = service.record_permission(
        actor_id="user-1",
        action="tool.execute",
        outcome="denied",
        session_id="session-1",
        request_id="request-1",
        reason_code="approval_required",
        metadata={
            "decision": "deny",
            "provider": "offline",
            "prompt": "private prompt",
            "path": "C:/private/source.py",
            "api_key": "sk-proj-private-value",
        },
    )
    service.record_tool(
        actor_id="user-1",
        action="tool.execute",
        outcome="succeeded",
        session_id="session-1",
        tool_id="read_file",
        metadata={"duration_ms": 12, "source": "private source"},
    )

    events = service.query(session_id="session-1")
    assert events[0] == event
    assert events[0].metadata == {"decision": "deny", "provider": "offline"}
    assert service.verify_chain()
    raw = (tmp_path / "audit.sqlite3").read_bytes()
    assert b"private prompt" not in raw
    assert b"sk-proj-private-value" not in raw
    assert service.query(category=AuditCategory.TOOL)[0].tool_id == "read_file"


def test_audit_persists_retention_and_purges_old_records(tmp_path: Path) -> None:
    now = datetime(2026, 7, 19, tzinfo=UTC)
    service = AuditLogService(tmp_path / "audit.sqlite3", retention_days=7, clock=lambda: now)
    service.record_config(actor_id="user-1", action="config.update", outcome="succeeded")
    service.record_external_request(
        actor_id="user-1",
        action="provider.request",
        outcome="succeeded",
        request_id="request-2",
    )
    with sqlite3.connect(tmp_path / "audit.sqlite3") as connection:
        connection.execute(
            "UPDATE audit_events SET created_at = ? WHERE request_id = 'request-2'",
            ((now - timedelta(days=8)).isoformat(),),
        )

    assert AuditLogService(tmp_path / "audit.sqlite3").retention_days == 7
    assert service.purge_expired() == 1
    assert [event.action for event in service.query()] == ["config.update"]
    assert service.verify_chain()


def test_audit_session_and_global_clear_are_explicit_and_physical(tmp_path: Path) -> None:
    path = tmp_path / "audit.sqlite3"
    service = AuditLogService(path)
    service.record_permission(
        actor_id="user-1", action="permission.check", outcome="allowed", session_id="keep"
    )
    service.record_tool(
        actor_id="user-1", action="tool.execute", outcome="failed", session_id="remove"
    )
    with pytest.raises(PermissionError, match="explicit confirmation"):
        service.clear_session("remove")

    assert service.clear_session("remove", confirm=True) == 1
    assert [event.session_id for event in service.query()] == ["keep"]
    assert service.verify_chain()
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0] == 1

    with pytest.raises(PermissionError, match="explicit confirmation"):
        service.clear_all()
    assert service.clear_all(confirm=True) == 1
    assert service.query() == ()
    assert service.verify_chain()


def test_audit_chain_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "audit.sqlite3"
    service = AuditLogService(path)
    service.record_config(actor_id="user-1", action="config.update", outcome="succeeded")
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE audit_events SET outcome = 'tampered'")
    assert not service.verify_chain()


def test_record_rejects_unknown_category_and_query_bounds(tmp_path: Path) -> None:
    service = AuditLogService(tmp_path / "audit.sqlite3")
    with pytest.raises(TypeError, match="AuditCategory"):
        service.record(
            actor_id="user-1", category="tool", action="run", outcome="succeeded"  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="limit"):
        service.query(limit=0)
    event = service.record_config(actor_id="u", action="x", outcome="ok")
    assert json.loads(json.dumps(event.to_dict()))
