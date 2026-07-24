# RC-212 Evidence

## Scope

Added `prompt_optimizer.audit.AuditLogService`, an independent SQLite audit
store for permission, tool, configuration, and external-request decisions.
Events persist UTC time, actor, outcome, session/request/tool/task identifiers,
an optional reason code, and a SHA-256 predecessor chain. Metadata is limited
to a small allowlist; prompt, source, path, credential, and unknown fields are
discarded before serialization.

Retention is persisted per audit database and can be set to a non-negative day
count or unlimited. Expired records, one session, or the complete audit store
can be deleted; destructive session/global operations require explicit
confirmation. Cleanup rebuilds the remaining chain and runs WAL truncation and
`VACUUM` so deleted rows are no longer queryable.

## Verification

- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc212_audit.py -q`: 5 passed.
- RC-211/RC-212 combined regression: 8 passed.
- Ruff, strict Mypy, compileall, `scripts/security_scan.py --check`,
  `scripts/check_rc_traceability.py --check`, and `scripts/check_delivery_plan.py`: passed.

Tests cover persistence across service instances, metadata exclusion,
tamper detection, retention purge, session/global confirmation gates, physical
row deletion, and chain re-anchoring after cleanup.

## Residual limits

This item provides the backend storage contract; GUI/API audit browsing and
cross-process stress/failure injection remain integration work for later
observability and database hardening items.
