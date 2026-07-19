from __future__ import annotations

from typing import Any

import pytest
from backend.rabbit_code.extensions import (
    CallableExtensionAdapter,
    ExtensionKind,
    ExtensionManager,
    ExtensionPermission,
    ExtensionPermissionDenied,
    ExtensionSpec,
)

# RC ID: RC-099. Verify declared capabilities, session approval, revocation, and adapters.


def _spec(name: str = "browser_demo") -> ExtensionSpec:
    return ExtensionSpec(
        name=name,
        kind=ExtensionKind.BROWSER,
        description="Controlled browser example",
        permissions=frozenset(
            {ExtensionPermission.NETWORK, ExtensionPermission.WORKSPACE_WRITE}
        ),
    )


def test_extensions_are_disabled_until_session_approval() -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    manager = ExtensionManager()
    manager.install(
        _spec(),
        CallableExtensionAdapter(lambda action, payload: calls.append((action, dict(payload)))),
    )

    with pytest.raises(ExtensionPermissionDenied, match="disabled"):
        manager.invoke(
            "session-a",
            "browser_demo",
            "fetch",
            {"url": "https://example.test"},
            required_permissions={ExtensionPermission.NETWORK},
        )
    assert calls == []

    manager.approve(
        "session-a",
        "browser_demo",
        {ExtensionPermission.NETWORK},
        explicit_confirmation=True,
    )
    manager.invoke(
        "session-a",
        "browser_demo",
        "fetch",
        {"url": "https://example.test"},
        required_permissions={ExtensionPermission.NETWORK},
    )
    assert calls == [("fetch", {"url": "https://example.test"})]


def test_write_and_network_permissions_are_independent_and_revocable() -> None:
    manager = ExtensionManager()
    manager.install(_spec("database_demo"), CallableExtensionAdapter(lambda action, payload: "ok"))
    manager.approve(
        "session-a",
        "database_demo",
        {ExtensionPermission.NETWORK},
        explicit_confirmation=True,
    )
    with pytest.raises(ExtensionPermissionDenied, match="workspace_write"):
        manager.invoke(
            "session-a",
            "database_demo",
            "write",
            {},
            required_permissions={ExtensionPermission.WORKSPACE_WRITE},
        )
    manager.revoke("session-a", "database_demo")
    with pytest.raises(ExtensionPermissionDenied, match="disabled"):
        manager.invoke(
            "session-a",
            "database_demo",
            "read",
            {},
            required_permissions={ExtensionPermission.NETWORK},
        )
    assert manager.audit[-1].allowed is False


def test_undeclared_permission_and_implicit_approval_are_rejected() -> None:
    manager = ExtensionManager()
    manager.install(
        ExtensionSpec(
            "service_demo",
            ExtensionKind.EXTERNAL_SERVICE,
            "Controlled service example",
            frozenset(),
        ),
        CallableExtensionAdapter(lambda action, payload: "ok"),
    )
    with pytest.raises(ExtensionPermissionDenied, match="explicit confirmation"):
        manager.approve("session-a", "service_demo", set())
    with pytest.raises(ExtensionPermissionDenied, match="did not declare"):
        manager.approve(
            "session-a",
            "service_demo",
            {ExtensionPermission.NETWORK},
            explicit_confirmation=True,
        )


def test_all_extension_kinds_use_the_same_adapter_boundary() -> None:
    manager = ExtensionManager()
    for kind in ExtensionKind:
        name = f"example_{kind.value}"
        manager.install(
            ExtensionSpec(name, kind, f"{kind.value} adapter", frozenset()),
            CallableExtensionAdapter(
                lambda action, payload, current_kind=kind: current_kind.value
            ),
        )
        manager.approve("session-a", name, set(), explicit_confirmation=True)
        assert manager.invoke("session-a", name, "read", {}) == kind.value
    assert len(manager.list_extensions()) == len(ExtensionKind)
