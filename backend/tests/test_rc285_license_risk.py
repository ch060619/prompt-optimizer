"""RC ID: RC-285. Tests for automated license risk scanning."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "docs" / "research" / "license-risk-policy.yml"
SCANNER = ROOT / "scripts" / "scan_license_risks.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc285_license_risk.py"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class TestPolicy:
    def test_exists(self) -> None:
        assert POLICY_PATH.is_file()

    def test_has_allow_category(self) -> None:
        data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        assert "allow" in data
        assert "MIT" in data["allow"]

    def test_has_review_category(self) -> None:
        data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        assert "review" in data
        assert "UNKNOWN" in data["review"]

    def test_has_deny_category(self) -> None:
        data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        assert "deny" in data
        assert "GPL-3.0" in data["deny"]
        assert "AGPL-3.0" in data["deny"]

    def test_has_exceptions(self) -> None:
        data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        assert "exceptions" in data
        for exc in data["exceptions"]:
            assert "package" in exc
            assert "license" in exc
            assert "owner" in exc
            assert "scope" in exc
            assert "expires" in exc

    def test_mpl_in_allow(self) -> None:
        data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        assert "MPL-2.0" in data["allow"]


class TestScanner:
    def test_exists(self) -> None:
        assert SCANNER.is_file()

    def test_scans_npm(self) -> None:
        text = SCANNER.read_text(encoding="utf-8")
        assert "scan_npm_deps" in text

    def test_scans_python(self) -> None:
        text = SCANNER.read_text(encoding="utf-8")
        assert "scan_python_deps" in text

    def test_scans_models(self) -> None:
        text = SCANNER.read_text(encoding="utf-8")
        assert "scan_model_deps" in text

    def test_has_classify_function(self) -> None:
        text = SCANNER.read_text(encoding="utf-8")
        assert "classify_license" in text

    def test_has_check_mode(self) -> None:
        text = SCANNER.read_text(encoding="utf-8")
        assert "--check" in text

    def test_has_json_output(self) -> None:
        text = SCANNER.read_text(encoding="utf-8")
        assert "--json" in text

    def test_has_scan_all(self) -> None:
        text = SCANNER.read_text(encoding="utf-8")
        assert "scan_all" in text


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_checks_policy(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_policy_exists" in text

    def test_checks_scanner(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_scanner_exists" in text

    def test_checks_ci(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_ci_integration" in text


class TestCIIntegration:
    def test_ci_has_license_scan(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "license-scan" in text or "scan_license_risks" in text

    def test_ci_has_rc285_reference(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "RC-285" in text


class TestPolicyCategories:
    """Verify policy categories are mutually exclusive."""

    def test_no_overlap_allow_deny(self) -> None:
        data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        allow = set(data.get("allow", []))
        deny = set(data.get("deny", []))
        assert allow.isdisjoint(deny), "Allow and deny categories must not overlap"

    def test_no_overlap_allow_review(self) -> None:
        data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        allow = set(data.get("allow", []))
        review = set(data.get("review", []))
        assert allow.isdisjoint(review), "Allow and review categories must not overlap"
