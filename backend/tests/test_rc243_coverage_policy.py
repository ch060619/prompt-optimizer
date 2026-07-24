from __future__ import annotations

from scripts.check_rc243_coverage import POLICY

# RC ID: RC-243. Keep coverage and critical-path policy itself testable.


def test_coverage_policy_declares_required_thresholds_and_paths() -> None:
    import yaml

    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    assert policy["thresholds"]["overall_percent"] > 0
    assert policy["thresholds"]["changed_files_percent"] > 0
    assert policy["critical_paths"]
    assert policy["mutation_checks"]
