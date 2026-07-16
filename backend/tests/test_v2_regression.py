from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

# RC ID: RC-047. Freeze V2 behavior before Rabbit Code migration work begins.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = REPOSITORY_ROOT / "scripts" / "generate_v2_regression_baseline.py"
GOLDEN_PATH = REPOSITORY_ROOT / "backend" / "tests" / "golden" / "v2_regression.json"
SPEC = importlib.util.spec_from_file_location("generate_v2_regression_baseline", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
baseline_generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = baseline_generator
SPEC.loader.exec_module(baseline_generator)


def _load_baseline() -> dict[str, object]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_v2_outputs_match_approved_golden_baseline() -> None:
    baseline = _load_baseline()

    assert baseline_generator.build_snapshot(REPOSITORY_ROOT) == baseline["snapshot"]


def test_baseline_update_has_explicit_rc_approval_and_migration_note() -> None:
    baseline = _load_baseline()
    approval = baseline["approval"]
    assert isinstance(approval, dict)
    assert approval["rc_id"] == "RC-047"
    assert approval["reason"]
    assert re.fullmatch(r"[0-9a-f]{40}", approval["source_commit"])

    note_path = REPOSITORY_ROOT / approval["migration_note"]
    assert note_path.is_file()
    assert "RC ID: RC-047" in note_path.read_text(encoding="utf-8")


def test_v2_golden_snapshot_covers_core_semantics() -> None:
    snapshot = _load_baseline()["snapshot"]
    assert isinstance(snapshot, dict)

    rules = snapshot["rules"]
    assert [rule["id"] for rule in rules] == [
        "clarity",
        "specificity",
        "context",
        "output_format",
        "constraints",
        "role",
        "examples",
        "actionability",
    ]
    assert snapshot["analysis"]["weak"]["suggestions"]
    assert snapshot["analysis"]["strong"]["score"]["total_score"] > 60
    assert snapshot["templates"]["rendered"].count("Python") == 1
    assert "输出要求" in snapshot["optimization"]["optimized_prompt"]
    assert [item["id"] for item in snapshot["history"]] == [2, 1]
    assert snapshot["diff"]["diff_lines"]
    assert set(snapshot["exports"]) == {"csv", "json", "md", "txt"}
    assert "平均分数变化" in snapshot["evaluation"]


def test_baseline_generator_rejects_a_migration_note_for_another_rc(tmp_path: Path) -> None:
    note = tmp_path / "migration.md"
    note.write_text("RC ID: RC-999\n", encoding="utf-8")

    with pytest.raises(ValueError, match="approving RC ID"):
        baseline_generator._relative_migration_note(tmp_path, note, "RC-047")
