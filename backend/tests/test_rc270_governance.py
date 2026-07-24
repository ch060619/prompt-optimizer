from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _form(path: str) -> dict[str, object]:
    payload = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _body_ids(form: dict[str, object]) -> set[str]:
    body = form.get("body")
    assert isinstance(body, list)
    return {str(item["id"]) for item in body if isinstance(item, dict) and "id" in item}


def test_issue_forms_require_rc_id_and_verifiable_context() -> None:
    bug = _form(".github/ISSUE_TEMPLATE/bug_report.yml")
    feature = _form(".github/ISSUE_TEMPLATE/feature_request.yml")

    assert {"rc_id", "reproduction", "environment", "verification"} <= _body_ids(bug)
    assert {"rc_id", "outcome", "scope", "provenance"} <= _body_ids(feature)


def test_public_issue_config_routes_security_to_private_advisories() -> None:
    config = _form(".github/ISSUE_TEMPLATE/config.yml")
    assert config["blank_issues_enabled"] is False
    contacts = config["contact_links"]
    assert isinstance(contacts, list)
    security_links = [item for item in contacts if "security" in str(item.get("name", "")).lower()]
    assert security_links
    assert "security/advisories/new" in str(security_links[0]["url"])


def test_governance_documents_and_pr_template_are_present() -> None:
    required = (
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "ROADMAP.md",
        "CHANGELOG.md",
        "docs/community/discussions.md",
        ".github/pull_request_template.md",
    )
    for relative in required:
        assert (ROOT / relative).is_file(), relative
    pull_request = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
    assert "RC ID" in pull_request
    assert "Verification" in pull_request
    assert "Provenance" in pull_request
    assert "Compatibility and data boundary" in pull_request
