from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# RC ID: RC-043. Traceability is a repository-level contract loaded from the root script.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "check_rc_traceability.py"
SPEC = importlib.util.spec_from_file_location("check_rc_traceability", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
traceability = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = traceability
SPEC.loader.exec_module(traceability)


def test_master_plan_has_all_unique_rc_ids() -> None:
    requirements = traceability.load_requirements(
        REPOSITORY_ROOT / "docs" / "rabbit-code-310-detailed-execution.md"
    )

    assert list(requirements) == [f"RC-{number:03d}" for number in range(1, 311)]


def test_required_templates_declare_rc_id() -> None:
    assert traceability.validate_templates(REPOSITORY_ROOT) == []


def test_report_marks_orphan_requirements_and_code_red(tmp_path: Path) -> None:
    (tmp_path / "backend" / "src").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    linked_id = "RC-" + "001"
    (tmp_path / "backend" / "src" / "linked.py").write_text(
        f'"""RC ID: {linked_id}. Linked implementation."""\n', encoding="utf-8"
    )
    (tmp_path / "backend" / "src" / "orphan.py").write_text(
        '"""Legacy implementation."""\n', encoding="utf-8"
    )
    (tmp_path / "docs" / "note.md").write_text(f"RC ID: {linked_id}.\n", encoding="utf-8")

    requirements = {
        "RC-001": "Linked requirement",
        "RC-002": "Orphan requirement",
    }
    references, orphan_code = traceability.scan_references(tmp_path, requirements)
    report = traceability.render_markdown(requirements, references, orphan_code)

    assert "| RC-001 | GREEN |" in report
    assert "| RC-002 | RED |" in report
    assert "backend/src/orphan.py" in report
    assert "backend/src/linked.py" not in orphan_code


def test_committed_reverse_index_matches_repository() -> None:
    requirements = traceability.load_requirements(
        REPOSITORY_ROOT / "docs" / "rabbit-code-310-detailed-execution.md"
    )
    references, orphan_code = traceability.scan_references(REPOSITORY_ROOT, requirements)
    expected = traceability.render_markdown(requirements, references, orphan_code)
    actual = (REPOSITORY_ROOT / "docs" / "traceability" / "rc-index.md").read_text(
        encoding="utf-8"
    )

    assert actual == expected
