from __future__ import annotations

import json
import threading
from pathlib import Path

from backend.rabbit_code.permissions import PermissionMode
from backend.rabbit_code.shared_surface import (
    ModelDescriptor,
    ProviderReference,
    SharedSurfaceContext,
    SurfaceClient,
    SurfaceKind,
)

# RC ID: RC-106. Verify CLI/GUI share provider, model, session, permission, and optimizer state.


class FakeOptimizer:
    def optimize(self, prompt: str, *, provider: str, model: str) -> str:
        return f"{provider}/{model}: {prompt}"


def _context(tmp_path: Path) -> SharedSurfaceContext:
    context = SharedSurfaceContext.create(
        tmp_path,
        FakeOptimizer(),
        state_path=tmp_path / "shared-surface.json",
    )
    context.configure_provider(ProviderReference("offline", "local://offline", "key-ref"))
    context.set_model_catalog((ModelDescriptor("local-model", "offline", frozenset({"text"})),))
    context.select_model("local-model")
    context.set_session("session-1")
    return context


def test_cli_and_gui_clients_read_the_same_snapshot_and_optimizer(tmp_path: Path) -> None:
    context = _context(tmp_path)
    cli = SurfaceClient(SurfaceKind.CLI, context)
    gui = SurfaceClient(SurfaceKind.GUI, context)

    assert cli.snapshot() == gui.snapshot()
    assert cli.optimize("hello") == gui.optimize("hello") == "offline/local-model: hello"
    assert cli.snapshot().to_dict()["provider"]["api_key_ref"] == "key-ref"
    assert "secret" not in str(cli.snapshot().to_dict())


def test_shared_changes_are_visible_to_both_surfaces_and_permission_is_explicit(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    cli = SurfaceClient(SurfaceKind.CLI, context)
    gui = SurfaceClient(SurfaceKind.GUI, context)

    context.set_permission_mode(PermissionMode.EDIT)
    context.set_session("session-2")

    assert cli.snapshot().session_id == "session-2"
    assert gui.snapshot().permission_mode is PermissionMode.EDIT


def test_provider_model_and_optimizer_require_shared_selection(tmp_path: Path) -> None:
    context = SharedSurfaceContext.create(tmp_path, FakeOptimizer())
    try:
        context.optimize("prompt")
    except ValueError as exc:
        assert "provider and model" in str(exc)
    else:
        raise AssertionError("unselected shared state must reject optimization")


def test_independent_contexts_reload_persisted_state_and_serialize_writes(tmp_path: Path) -> None:
    state_path = tmp_path / "shared-surface.json"
    first = _context(tmp_path)
    second = SharedSurfaceContext.create(
        tmp_path,
        FakeOptimizer(),
        state_path=state_path,
    )

    assert second.snapshot() == first.snapshot()

    barrier = threading.Barrier(2)

    def update_session(context: SharedSurfaceContext, session_id: str) -> None:
        barrier.wait()
        context.set_session(session_id)

    workers = [
        threading.Thread(target=update_session, args=(first, "session-a")),
        threading.Thread(target=update_session, args=(second, "session-b")),
    ]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    final = SharedSurfaceContext.create(
        tmp_path,
        FakeOptimizer(),
        state_path=state_path,
    )
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert final.snapshot().session_id in {"session-a", "session-b"}
    assert persisted["provider"]["api_key_ref"] == "key-ref"
    assert "sk-secret" not in state_path.read_text(encoding="utf-8")
