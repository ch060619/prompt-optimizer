# RC-210 Evidence

## Scope

Added `TelemetryService` with closed-by-default consent. Technical metadata is
recorded only after explicit opt-in; prompt, source, code, command, raw output,
and similar content fields are dropped unless content telemetry is separately
selected. Consent can be revoked and pending events can be cleared.

Added `DiagnosticBundleService` for preview, export, clear, and send. The
preview contains only sanitized metadata and file names/sizes, never source,
prompt, or log contents. Export and send require explicit confirmation, and a
rejected action never calls its sender. The GUI Diagnostics page now opens a
redacted preview before copying and supports clearing that preview.

## Verification

- `python -m pytest backend/tests/test_rc210_privacy.py backend/tests/test_rc093_diagnostics.py backend/tests/test_rc180_redaction.py -q`: 9 passed.
- `python -m ruff check` for privacy, diagnostics, redaction, and RC-210 test files: passed.
- `python -m mypy --strict --explicit-package-bases` with `MYPYPATH=backend/src;backend;packages/protocol` for privacy and RC-210 tests: passed.
- `python -m compileall -q` for privacy and RC-210 tests: passed.
- `npm test -- --run tests/Diagnostics.test.tsx` from `frontend`: 4 passed.
- `npm run lint` and `npm run build` from `frontend`: passed.

Tests cover default no-op telemetry, explicit opt-in, content exclusion,
revocation, clearing, secret/prompt/source redaction, preview generation,
confirmation rejection, export, send, and GUI preview clearing.

## Residual limits

No real telemetry or support endpoint was contacted. The sender is injected at
the service boundary so default and rejected paths can prove no network side
effect; endpoint configuration and crash collector deployment remain release
configuration work.
