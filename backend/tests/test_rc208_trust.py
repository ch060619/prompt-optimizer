from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from backend.rabbit_code.plugins import PluginRegistry, PluginStateError
from backend.rabbit_code.trust import (
    TrustApprovalRequired,
    TrustExecutionContext,
    TrustManifest,
    TrustReapprovalRequired,
    TrustRegistry,
)

# RC ID: RC-208. Verify manifest provenance, hash changes, disable, lock, and isolation.


def _manifest(name: str = "demo", *, digest: str | None = None) -> TrustManifest:
    return TrustManifest(
        kind="plugin",
        name=name,
        version="1.0.0",
        source="local",
        sha256=digest or hashlib.sha256(b"artifact").hexdigest(),
        permissions=frozenset({"read"}),
    )


def test_trust_registry_requires_explicit_approval_and_runs_isolated_context() -> None:
    registry = TrustRegistry(allowed_sources={"local"}, allowed_permissions={"read"})
    manifest = _manifest()
    with pytest.raises(TrustApprovalRequired):
        registry.register(manifest)

    record = registry.register(manifest, explicit_confirmation=True)
    assert record.enabled
    assert registry.list_records()[0].manifest == manifest
    seen: list[TrustExecutionContext] = []

    def handler(context: TrustExecutionContext, payload: Mapping[str, Any]) -> int:
        seen.append(context)
        return int(payload["value"]) + 1

    result = registry.execute(
        "plugin:demo",
        {"value": 2},
        handler,
    )
    assert result == 3
    assert seen[0].isolated
    assert seen[0].permissions == frozenset({"read"})


def test_source_change_requires_reapproval_and_lock_blocks_update() -> None:
    registry = TrustRegistry(allowed_sources={"local"}, allowed_permissions={"read"})
    registry.register(_manifest(), explicit_confirmation=True)
    changed = _manifest(digest=hashlib.sha256(b"changed").hexdigest())
    with pytest.raises(TrustReapprovalRequired):
        registry.register(changed)
    registry.lock("plugin:demo")
    with pytest.raises(TrustReapprovalRequired, match="locked"):
        registry.register(changed, explicit_confirmation=True)
    registry.disable("plugin:demo")
    with pytest.raises(PermissionError, match="disabled"):
        registry.execute("plugin:demo", {}, lambda _context, _payload: "not-run")
    registry.revoke("plugin:demo")
    assert registry.list_records()[0].enabled is False


def test_manifest_kinds_and_permissions_are_declared_before_install() -> None:
    registry = TrustRegistry(allowed_sources={"local"}, allowed_permissions={"read"})
    for kind in ("skill", "hook", "mcp", "script"):
        manifest = TrustManifest(
            kind=kind,
            name=f"{kind}-one",
            version="1.0.0",
            source="local",
            sha256="a" * 64,
            permissions=frozenset({"read"}),
        )
        registry.register(manifest, explicit_confirmation=True)

    with pytest.raises(PermissionError, match="permission"):
        registry.register(
            TrustManifest(
                kind="script",
                name="danger",
                version="1.0.0",
                source="local",
                sha256="b" * 64,
                permissions=frozenset({"shell"}),
            ),
            explicit_confirmation=True,
        )


def test_plugin_lock_and_runtime_hash_recheck_require_reapproval(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    artifact = package / "plugin.py"
    artifact.write_text("trusted\n", encoding="utf-8")
    manifest = {
        "name": "plugin-one",
        "version": "1.0.0",
        "entrypoint": "plugin.handler",
        "permissions": ["read"],
        "source": "local",
        "min_app_version": "3.0.0",
        "artifact": "plugin.py",
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    registry = PluginRegistry(
        tmp_path / "installed",
        handlers={"plugin.handler": lambda _context: "ok"},
    )

    registry.install(package)
    registry.enable("plugin-one")
    registry.lock("plugin-one")
    with pytest.raises(PluginStateError, match="unlock"):
        registry.upgrade(package)
    installed_artifact = tmp_path / "installed" / "plugin-one" / "1.0.0" / "plugin.py"
    installed_artifact.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(PluginStateError, match="source changed"):
        registry.execute("plugin-one", {})
    assert not registry.get("plugin-one").enabled
