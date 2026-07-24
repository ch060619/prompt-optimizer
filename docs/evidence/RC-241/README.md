# RC-241 Evidence

## Scope

Moved `RABBIT_CODE_REAL_PROVIDER_TESTS=0` to the backend CI job environment, keeping every
ordinary push/PR test path Mock/offline by default. Added
`scripts/check_rc241_ci_mock.py`, `backend/tests/test_rc241_ci_mock.py`, and the explicit
manual Provider policy at `docs/ci/provider-test-policy.md`.

## Verification

```text
python scripts/check_rc241_ci_mock.py
python -m pytest backend/tests/test_rc241_ci_mock.py backend/tests/test_rc231_provider_contracts.py -q
.venv\Scripts\ruff.exe check scripts/check_rc241_ci_mock.py backend/tests/test_rc241_ci_mock.py
```

Results: CI policy gate passed; Mock contract suite and policy test passed; Ruff passed.

## Limits

Real Provider/model calls were intentionally not run. The manual matrix requires user-owned
credentials or local hardware and explicit confirmation outside ordinary CI.
