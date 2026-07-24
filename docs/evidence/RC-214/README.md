# RC-214 Evidence

## Scope

Added SQLite schema version 2 execution through SQLiteMigrationRunner.
Migrations run inside BEGIN IMMEDIATE, which serializes writers before the
script changes schema. The runner validates supported versions, required
tables, rollback on script errors, and the migration history row.

Storage connections now set busy timeout, foreign keys, synchronous NORMAL,
and WAL is established during initialization. The storage layer adds indexes
for owner/workspace/task lookup and makes default-project creation plus
prompt-version insertion a single transaction. Existing backup/restore
operations continue to verify SQLite integrity; startup now rejects a corrupt
database before migration.

## Verification

- .venv\Scripts\python.exe -m pytest backend/tests/test_rc214_sqlite_hardening.py backend/tests/test_storage_backup.py backend/tests/test_rc064_storage_boundary.py backend/tests/test_storage_export.py -q: 17 passed.
- RC-214 tests cover concurrent migration application, migration rollback,
  schema/index/PRAGMA checks, atomic composite writes, corrupt-database
  rejection, backup, restore, concurrent writes, and atomic file boundaries.
- Targeted Ruff, strict Mypy, compileall, generated data-model drift, and
  scripts/workspace.py check: passed.
- Current backend full regression: 646 passed, 9 skipped, 2 deprecation
  warnings. Frontend: 23 test files, 109 passed.

## Residual limits

No full-regression failures remain. No real power-loss or cross-platform
filesystem crash matrix was executed.
