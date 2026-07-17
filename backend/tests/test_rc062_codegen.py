from __future__ import annotations

from pathlib import Path

from scripts.generate_api import check_generated

# RC ID: RC-062. Verify generated API artifacts and the non-duplicating type export.
ROOT = Path(__file__).parents[2]


def test_generated_typescript_artifacts_match_openapi() -> None:
    check_generated()


def test_frontend_types_only_reexport_generated_api_schemas() -> None:
    types_source = (ROOT / "frontend" / "src" / "types.ts").read_text(encoding="utf-8")

    assert "./generated/schema" in types_source
    assert "interface " not in types_source
    assert "type Priority" not in types_source
