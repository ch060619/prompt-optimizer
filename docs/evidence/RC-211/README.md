# RC-211 Evidence

## Scope

Added the repository security baseline for RC-211: a data-flow and STRIDE
threat model, private vulnerability reporting and response targets, credential
rotation policy, deterministic repository secret scanning, Dockerfile rules,
CycloneDX SBOM generation, and SBOM drift checking. CI runs the deterministic
gate plus Ruff, strict Mypy, `pip-audit`, and production-only `npm audit`.

## Verification

- `.venv\Scripts\python.exe scripts/security_scan.py --check`: passed.
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc211_security_engineering.py -q`: 3 passed.
- Ruff, strict Mypy, and compileall for the RC-211 files: passed.
- Negative tests detect a provider key and reject `latest`, `ADD`, `npm install`, and a root-only Dockerfile.
- A live `pip-audit --local` run against the repaired `.venv` reports no known
  vulnerabilities. The audit initially found vulnerable `idna`, Starlette,
  pip, and stale PyJWT; project constraints and the local build tool were
  upgraded, and the orphaned V2 dependency was removed before re-audit.

## Residual limits

The current environment still does not provide `syft`, `trivy`, `grype`, or
`gitleaks`; the deterministic repository scanner and CycloneDX drift gate run
locally, while external container scanners remain CI/platform tools. The local
project package itself is skipped by `pip-audit` because it is not a PyPI
release; all installed third-party packages were audited.
