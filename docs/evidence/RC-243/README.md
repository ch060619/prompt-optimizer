# RC-243 Evidence

## Scope

Added `docs/testing/coverage-policy.yml`, `scripts/check_rc243_coverage.py`, and
`backend/tests/test_rc243_coverage_policy.py`. The policy requires an overall coverage
threshold, a changed-files threshold, and explicit test lists for permissions, secrets,
installation, migration, cancellation, recovery, and mutation/fault checks. CI writes the
JSON report before running the policy gate.

## Verification

```text
pytest --cov=prompt_optimizer --cov-report=term-missing --cov-report=json:docs/evidence/RC-243/coverage-report.json backend/tests
python scripts/check_rc243_coverage.py --check
python -m pytest backend/tests/test_rc243_coverage_policy.py -q
.venv\Scripts\ruff.exe check scripts/check_rc243_coverage.py backend/tests/test_rc243_coverage_policy.py
```

The full offline backend run collected 727 tests and recorded 85.99% overall
coverage. The four changed files reported 97.56% (`core/optimizer.py`), 95.27%
(`services.py`), 88.22% (`local_install.py`), and 81.93% (`model_lifecycle.py`).
The RC-243 policy test passed and the coverage gate reported 17 critical-path
tests present. After regenerating the reverse index, the final full backend
run passed with 718 passed, 9 skipped, and 2 warnings; the traceability suite
passed with 4 tests.

## Limits

Mutation testing is represented by explicit fault-injection regression files in the policy;
no third-party mutation runner is required for ordinary CI. Real external Provider/model
coverage remains outside this offline gate.
