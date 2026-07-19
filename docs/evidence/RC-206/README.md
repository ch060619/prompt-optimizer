# RC-206 Evidence

## Scope

Added `SensitiveFilePolicy` with default detection for dotenv files, SSH/key
material, cloud configuration, browser profiles, and system directories, plus
user filename/path-prefix rules. Sensitive reads and sends are independently
approval-gated; FileTools hides sensitive entries from list/search by default
and requires explicit approval to read. `SecretScanner` reports only finding
kind, line, and digest, never the secret value, and blocks non-clean output.

## Verification

- `python -m pytest backend/tests/test_rc206_sensitive_files.py backend/tests/test_rc090_file_tools.py -q`: 7 passed, 1 skipped.
- `python -m ruff check` for sensitive-file, FileTools, package exports, and RC-206 tests: passed.
- `python -m mypy --strict` for sensitive-file and FileTools modules: passed.

Tests cover `.env`/SSH detection, custom rules, default list/search exclusion,
separate read/send approvals, private-key/API-key scanning, metadata-only
findings, and permission-mode independence.

## Residual limits

No real browser profile, cloud credential, system directory, or external
Provider send was used. Secret pattern coverage remains conservative and is
intentionally a blocking scanner, not a claim of complete secret detection.
