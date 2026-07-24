# Rabbit Code Governance Policy

## Maintainer Permissions

### Roles

| Role | Permissions | Granted By |
| --- | --- | --- |
| **Contributor** | Open issues, submit PRs | Anyone |
| **Triage** | Label/close issues, manage project board | Existing maintainers |
| **Write** | Push to branches, review/merge PRs (non-release) | Existing maintainers |
| **Maintain** | Manage releases, merge to `main`, manage CI | Existing maintainers |
| **Admin** | Repository settings, secrets, deletion | Repository owner |

### Permission Granting

- New maintainers are proposed by an existing maintainer and require approval from at least one other maintainer.
- Permission changes are tracked in the project board.
- No external corporate sponsorship of maintainer roles is permitted.

## Branch Protection

### `main` Branch

- **Require pull request before merging**: At least 1 approval from a maintainer.
- **Require status checks to pass**: CI (backend, frontend, docker, license-scan) must pass.
- **Require branches to be up to date**: PR must be rebased on latest `main`.
- **Do NOT require signed commits**: Per project policy, signed commits are not required.
- **Do NOT require signed tags**: Per project policy, signed tags are not required.
- **Require conversation resolution**: All review comments must be resolved before merge.
- **Restrict pushes that create new files in `docs/legal/`**: Legal documents require maintainer review.

### Release Branches (`release/*`)

- Created from `main` by a maintainer.
- Only bug fixes and documentation updates are allowed.
- Merged back to `main` after release.

## Release Approval

### Release Process

1. A maintainer creates a Git tag `vX.Y.Z` following Semantic Versioning.
2. The release workflow (`.github/workflows/release.yml`) triggers automatically.
3. The workflow builds artifacts, generates SBOM, and creates a GitHub Release.
4. For `stable` channel: Release is published immediately.
5. For `beta`/`nightly` channel: Release is created as draft/prerelease.
6. A maintainer reviews the draft release, edits notes if needed, and publishes.

### Release Checklist

Before tagging a release:

- [ ] All CI checks pass on `main`.
- [ ] `CHANGELOG.md` has an entry for the new version.
- [ ] `THIRD_PARTY_NOTICES.md` is up to date.
- [ ] License scan (`scan_license_risks.py --check`) passes with no denied licenses.
- [ ] SBOM generation (`generate_sbom.py`) succeeds.
- [ ] Desktop build succeeds on at least one platform.
- [ ] No known critical security vulnerabilities.

### Rollback

- Releases can be retracted by converting to draft.
- Users can rollback via `pip install rabbit-code==<previous-version>`.
- Database migrations are versioned (TARGET_SCHEMA_VERSION=2); rollback to older versions is blocked if schema is newer.

## Dependency Updates

### Policy

- Dependencies are updated via PR, not direct push to `main`.
- Major version updates require maintainer review.
- Security updates (patch versions for CVEs) can be fast-tracked with maintainer approval.
- `pip-audit` and `npm audit` results are checked in CI.

### Automated Updates

- Dependabot is enabled for Python and npm dependencies.
- Dependabot PRs follow the standard review process.
- Dependabot is configured for weekly checks.

### License Verification

- Every new dependency must pass `scan_license_risks.py --check`.
- Dependencies with `UNKNOWN` license require manual review before merge.
- Denied licenses (GPL, AGPL, SSPL, etc.) block the PR.

## Security Response

### Vulnerability Reporting

- Vulnerabilities are reported via GitHub Security Advisories (private).
- Public issues must NOT be used for vulnerability reports.
- Security advisories are triaged within 72 hours.

### Response Timeline

| Severity | Acknowledgment | Fix Release |
| --- | --- | --- |
| Critical | 24 hours | 7 days |
| High | 48 hours | 14 days |
| Medium | 72 hours | 30 days |
| Low | 1 week | Next release |

### Security Fixes

- Security fixes are developed in a private branch.
- A Security Advisory is published with the fix release.
- CVE IDs are requested for critical/high vulnerabilities.

### No Signed Commits

Per project policy:
- **Signed commits are NOT required.** Contributors are not required to set up GPG/SSH signing.
- **Signed tags are NOT required.** Release tags are unsigned.
- Identity is established through GitHub authentication and CODEOWNERS review.

## CODEOWNERS

The `CODEOWNERS` file defines automatic review requirements for sensitive paths:

```
# Sensitive paths require maintainer review
/docs/legal/           @maintainers
/docs/adr/             @maintainers
/.github/workflows/    @maintainers
/scripts/              @maintainers
/LICENSE               @maintainers
/NOTICE                @maintainers
/THIRD_PARTY_NOTICES.md @maintainers
```
