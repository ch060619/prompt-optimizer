from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.permissions import PermissionMode
from backend.rabbit_code.shared_surface import (
    ModelDescriptor,
    ProviderReference,
    SharedSurfaceConflict,
    SharedSurfaceContext,
)

# RC ID: RC-244. Verify CLI and GUI refresh the same workspace state and detect stale writes.


class FakeOptimizer:
    def optimize(self, prompt: str, *, provider: str, model: str) -> str:
        return f"{provider}/{model}: {prompt}"


def _context(root: Path) -> SharedSurfaceContext:
    return SharedSurfaceContext.create(
        root,
        FakeOptimizer(),
        state_path=root / "shared-surface.json",
    )


def test_cli_and_gui_refresh_all_cross_surface_state(tmp_path: Path) -> None:
    gui = _context(tmp_path)
    cli = _context(tmp_path)
    gui.configure_provider(ProviderReference("mock", "mock://provider", "key-ref"))
    gui.set_model_catalog((ModelDescriptor("mock-model", "mock", frozenset({"text"})),))
    gui.select_model("mock-model")
    gui.set_session("gui-session")
    gui.set_permission_mode(PermissionMode.EDIT)
    gui.record_prompt_version("v-1", accepted=True)
    gui.record_file_change(
        "src/example.py",
        before_sha256="before",
        after_sha256="after",
        checkpoint_id="checkpoint-1",
    )

    assert cli.snapshot() == gui.snapshot()
    assert cli.snapshot().to_dict()["file_changes"] == [
        {
            "path": "src/example.py",
            "before_sha256": "before",
            "after_sha256": "after",
            "checkpoint_id": "checkpoint-1",
        }
    ]
    assert [event.event_type for event in cli.events_since(0)] == [
        "provider.changed",
        "model_catalog.changed",
        "model.changed",
        "session.changed",
        "permission.changed",
        "prompt_version.changed",
        "file_change.changed",
    ]


def test_stale_cross_surface_write_returns_explicit_conflict(tmp_path: Path) -> None:
    gui = _context(tmp_path)
    cli = _context(tmp_path)
    stale_revision = cli.snapshot().revision

    gui.set_session("gui-session")

    with pytest.raises(SharedSurfaceConflict, match="shared state changed"):
        cli.update_optimistic(
            stale_revision,
            lambda state: state.update(session_id="stale-cli-session"),
            event_type="session.changed",
        )

    assert cli.snapshot().session_id == "gui-session"
