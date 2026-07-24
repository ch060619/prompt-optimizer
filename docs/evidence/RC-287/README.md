# RC-287: Maintainer Governance Policies

## Status

**Complete** — GOVERNANCE.md, SECURITY.md, and CODEOWNERS created. All policies documented. 26 tests passed.

## What Was Done

1. **Created `GOVERNANCE.md`** with 6 sections:
   - Maintainer Permissions: 5 roles (Contributor, Triage, Write, Maintain, Admin)
   - Branch Protection: main + release branches, PR required, CI must pass, no signed commits/tags
   - Release Approval: tag-triggered workflow, release checklist, rollback process
   - Dependency Updates: PR-based, major version review, Dependabot weekly, license verification
   - Security Response: private advisories, severity-based timeline (24h-1week ack)
   - CODEOWNERS: sensitive paths require maintainer review

2. **Created `SECURITY.md`**:
   - Private vulnerability reporting via GitHub Security Advisories
   - 72-hour acknowledgment commitment
   - Severity-based response timeline (Critical/High/Medium/Low)
   - Scope: CLI, Desktop, API, Frontend
   - User security best practices

3. **Created `.github/CODEOWNERS`**:
   - 8 sensitive path patterns requiring maintainer review
   - Covers: legal, ADRs, workflows, scripts, license files, security, governance, migrations

4. **Created `scripts/check_rc287_governance.py`** — 4 validation groups

5. **Created `backend/tests/test_rc287_governance.py`** — 26 tests across 6 classes

## Key Policy Decisions

| Policy | Decision |
| --- | --- |
| Signed commits | NOT required |
| Signed tags | NOT required |
| PR approval | 1 maintainer approval required |
| CI checks | backend + frontend + docker + license-scan must pass |
| Dependabot | Enabled, weekly |
| Security reporting | GitHub Security Advisories (private) |
| Release trigger | Git tag `v*` |

## Verification Results

- `python scripts/check_rc287_governance.py` → PASS
- `pytest backend/tests/test_rc287_governance.py -q` → 26 passed

## Limitations

- Branch protection rules must be configured in GitHub repository settings (documented in GOVERNANCE.md, not enforced by code)
- Dependabot configuration requires GitHub repository settings (documented in GOVERNANCE.md)
- Actual CODEOWNERS enforcement requires GitHub repository settings
