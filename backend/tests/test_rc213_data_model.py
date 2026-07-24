from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

from scripts.generate_data_model import OUTPUTS, load_schema, render

# RC ID: RC-213. Verify the shared schema, generated artifacts, and model types.


def test_core_schema_contains_required_entities_and_lifecycle_fields() -> None:
    schema = load_schema()
    names = {entity["name"] for entity in schema["entities"]}
    assert names == {
        "workspace",
        "session",
        "message",
        "content_block",
        "tool_call",
        "file_snapshot",
        "prompt_version",
        "provider_reference",
        "model_manifest",
        "setting",
    }
    for entity in schema["entities"]:
        field_names = {field["name"] for field in entity["fields"]}
        assert {"id", "deleted_at", "version"} <= field_names
        assert {"created_at", "captured_at"} & field_names


def test_generated_migration_and_cross_surface_types_are_current(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    outputs = render(load_schema())
    for name, path in OUTPUTS.items():
        assert path.read_text(encoding="utf-8") == outputs[name]

    migration = (root / "backend/migrations/0002_core_data_model.sql").read_text(
        encoding="utf-8"
    )
    with sqlite3.connect(tmp_path / "model.sqlite3") as connection:
        connection.executescript(migration)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "workspaces" in tables
    assert "prompt_versions_v2" in tables
    assert "settings" in tables
    assert "FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE" in migration

    module_path = root / "backend/src/prompt_optimizer/data_model.py"
    spec = importlib.util.spec_from_file_location("generated_data_model", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    workspace = module.WorkspaceData(
        id="workspace-1",
        owner_id=1,
        name="Test",
        created_at="2026-07-19T00:00:00+00:00",
        updated_at="2026-07-19T00:00:00+00:00",
    )
    assert workspace.version == 1
    assert json.loads(json.dumps(workspace.model_dump(mode="json")))
