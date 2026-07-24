# RC-219 Evidence

## Scope

Added the local `rc219-v1` metrics aggregator and `GET /api/v1/metrics`
report. It records request latency, success/failure counts and rates, actual
Provider token usage when reported, first non-empty stream delta latency,
tool call success counts, local runner model-load latency, and bounded CPU,
RAM, and GPU memory samples. Provider/model labels are technical IDs only;
prompt, source, path, credential, raw request, and response content do not
enter the snapshot. No upload or remote telemetry endpoint was added.

Metric definitions and units are documented in `docs/metrics/RC-219.md`.

## Verification

- `backend/tests/test_rc219_metrics.py`: 4 passed.
- Provider/RC-216 related regression: 20 passed, 1 skipped.
- Frontend: 22 test files, 106 passed; ESLint and Vite build passed.
- Targeted Ruff, strict Mypy, metrics content-boundary check, OpenAPI/client
  drift, traceability, and `scripts/workspace.py check` passed.
- Current full backend baseline: 646 passed, 9 skipped, 2 deprecation warnings;
  the earlier configuration, RC-141/RC-143, traceability, and V2 baseline
  failures are resolved. No RC-219 failure occurred.

## Residual limits

The metrics store is local and in-memory. CPU utilization and GPU memory can
be unavailable on a platform, and no real Provider request or external tool
execution was used. Explicit anonymous upload consent is specified for
RC-220, not implemented here.
