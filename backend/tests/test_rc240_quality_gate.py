from __future__ import annotations

from scripts.check_rc240_quality import build_report

# RC ID: RC-240. Keep score, semantic, structure, language, and grouping gates executable.


def test_offline_quality_gate_passes_fixed_dataset() -> None:
    report = build_report()

    assert report["passed"] is True
    assert report["dataset_version"] == "rc-158-v1"
    assert report["random_seed"] == 158
    assert len(report["cases"]) == 60
    assert report["groups"] == [
        {"provider": "offline", "model": "rules", "cases": 60, "average_score_delta": 72.8}
    ]
