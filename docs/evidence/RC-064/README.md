# RC-064 Execution Evidence

- RC ID: RC-064
- Status: PASS for the accepted local SQLite/file storage boundary
- Owner: Codex
- Implementation commit: `5c9ef99`
- Scope: Keep structured metadata in SQLite, move large payloads to versioned file categories, and
  verify transactional/concurrent writes, atomic replacement, crash cleanup, and cache isolation.

## Delivered

- Added `FileStore` with `v1/logs`, `v1/attachments`, `v1/models`, and `v1/cache` categories.
- Added path-key validation, process-local locking, complete-write plus `fsync`, atomic `os.replace`,
  and temporary-file cleanup on both success and failure.
- Exposed the file boundary from `StorageService` without moving existing metadata out of SQLite.
- Configured SQLite connections with a busy timeout, foreign keys, and WAL/synchronous settings;
  existing per-operation connection contexts remain the transaction boundary.
- Added concurrent same-file writes, concurrent SQLite version writes, injected replace failure,
  traversal rejection, versioned-directory, and cache cleanup isolation tests.
- Added `docs/adr/0009-sqlite-and-file-storage-boundary.md` with Accepted status and explicit limits.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest backend/tests/test_rc064_storage_boundary.py -q` | PASS: 4 passed |
| `python -m pytest backend/tests/test_rc064_storage_boundary.py backend/tests/test_storage_backup.py backend/tests/test_storage_export.py -q` | PASS: 12 passed |
| `python -m ruff check backend/src/prompt_optimizer/storage backend/tests/test_rc064_storage_boundary.py` | PASS |
| `python -m mypy backend/src/prompt_optimizer/storage` | PASS |
| `python scripts/workspace.py verify` | PASS: drift, traceability, delivery plan, Ruff, Mypy, backend 92 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC establishes a local filesystem/SQLite boundary. It does not claim encrypted attachments or
models, quotas, retention, cross-process file locks, distributed storage, or complete session-table
implementation. Existing migration and frontend jsdom warnings remain unrelated repository
conditions.

## Verification Note

The first root verification stopped because the newly added RC-064 evidence had not yet been
regenerated into the reverse index. After updating the plan and running
`python scripts/check_rc_traceability.py --write`, the complete root verification passed.

## Environment

- Time: 2026-07-17 16:51:31 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
