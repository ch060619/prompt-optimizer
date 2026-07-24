# RC-215 Evidence

## Scope

Added docs/logging/schema-v1.json and a matching Pydantic StructuredLogEvent.
StructuredLogEmitter is the single event construction boundary and carries
request_id, session_id, tool_id, and task_id for cross-service correlation.
Metadata is field-allowlisted; prompt, source, path, credential, key, token,
content, raw input/output, and unknown fields are omitted before JSON
serialization. Safe string values still pass through secret redaction.

The structured log schema and redaction check run from both CI and
scripts/workspace.py. FastAPI request middleware uses the same emitter, so
request lifecycle events do not bypass the structured logging boundary.

## Verification

- .venv\Scripts\python.exe -m pytest backend/tests/test_rc215_structured_logging.py -q: 3 passed.
- scripts/check_structured_logging.py: passed.
- RC-211 security scan: passed.
- Targeted Ruff, strict Mypy, traceability, and workspace check: passed.

Tests cover schema extra-field rejection, correlation identifiers, secret and
content exclusion, nested/unknown field dropping, JSON round-trip, and bounded
identifier input.

## Residual limits

No external log collector or Provider request was contacted. Existing public
output helpers remain compatible; future log rotation and retention controls
are handled by RC-218.
