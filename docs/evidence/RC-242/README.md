# RC-242 Evidence

## Scope

Updated `.github/workflows/ci.yml` so backend and frontend jobs run on both
`ubuntu-latest` and `windows-latest`, with fail-fast disabled. The matrix retains
traceability, generated API, dependency, security, SBOM, license, Ruff, Mypy, compile,
Pytest/Mock, frontend lint/test/build, and audit gates.

Added `scripts/check_rc242_ci_matrix.py` and
`backend/tests/test_rc242_ci_matrix.py` to keep the matrix and required command contract
explicit.

## Verification

```text
python scripts/check_rc242_ci_matrix.py
python -m pytest backend/tests/test_rc242_ci_matrix.py -q
.venv\Scripts\ruff.exe check scripts/check_rc242_ci_matrix.py backend/tests/test_rc242_ci_matrix.py
```

Results: matrix policy passed; focused test passed; Ruff passed. GitHub-hosted Windows and
Ubuntu execution is represented by workflow configuration and remains to run in CI.

## Limits

The current Tauri configuration has native bundling disabled, so this RC does not claim a
native desktop package build. The actual hosted matrix result is external CI state, not a
local Windows-only result.
