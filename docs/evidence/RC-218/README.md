# RC-218 Evidence

## Scope

Added a bounded local retention service with explicit defaults: `info` log
level, 5 MB per log file, 50 MB total logs, 100 MB cache, 30-day terminal
task/session retention, and 365-day/500-entry Prompt history retention.
Preview computes rotation, oldest-first file deletion, terminal task deletion,
history deletion, and estimated file bytes before any mutation. Confirmed
cleanup rotates oversized logs, deletes only `logs`/`cache` files, and removes
only eligible terminal tasks/history rows. `queued`/`running` tasks and
configuration, model, attachment, and database paths remain protected.

Settings now exposes the retention preview/confirm flow separately from the
existing destructive all-local-data flow; confirming retention does not clear
workspace settings.

## Verification

- `backend/tests/test_rc218_retention.py`: 4 passed.
- API contract/API, storage backup, RC-184 cleanup, and RC-218 regression:
  32 passed.
- Frontend: 22 test files, 106 passed; ESLint and Vite build passed.
- Targeted Ruff and strict Mypy passed.
- OpenAPI/client drift, traceability, and `scripts/workspace.py check` passed.

## Residual limits

The repository does not yet run a cross-platform file-lock, power-loss, or
real background scheduler matrix. Rotation and cleanup are available through
the local retention service and guarded by the process callback; no external
log collector or remote storage was contacted.
