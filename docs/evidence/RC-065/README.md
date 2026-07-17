# RC-065 Execution Evidence

- RC ID: RC-065
- Status: PASS for the accepted local layered-configuration boundary
- Owner: Codex
- Implementation commit: `421a585`
- Scope: Define default/user/workspace/session/CLI precedence, typed field metadata, sensitive-field
  policy, source inspection, and CLI display.

## Delivered

- Added `ConfigService` with deterministic `default < user < workspace < session < cli` merging.
- Registered field type, sensitivity, scope, nullable, allowed-layer, and minimum-value metadata.
- Added JSON loading for user/workspace layers and in-memory session/CLI layers; unknown fields,
  type mismatches, invalid ranges, and out-of-scope secret overrides fail explicitly.
- Added `ConfigSnapshot.values`, `source_of`, and safe `display` methods. Sensitive values are
  represented as `secret://config/<field>` and are never rendered in the source table.
- Added `rabbit config show` with workspace, user-config, session, and CLI override inputs.
- Added parameterized precedence tests, validation/sensitive-display tests, and CLI output tests.
- Added `docs/adr/0010-layered-configuration.md` with Accepted status and explicit Provider/env and
  OS-keychain migration limits.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest backend/tests/test_config.py -q` | PASS: 7 passed |
| `python -m pytest backend/tests/test_config.py backend/tests/test_cli_compatibility.py -q` | PASS: 10 passed |
| `python -m pytest backend/tests/test_identity_migration.py backend/tests/test_auth_boundary.py backend/tests/test_providers.py -q` | PASS: 15 passed |
| `python -m ruff check backend/src/prompt_optimizer/config backend/src/prompt_optimizer/cli/app.py backend/tests/test_config.py` | PASS |
| `python -m mypy backend/src/prompt_optimizer/config backend/src/prompt_optimizer/cli/app.py` | PASS |
| `python scripts/workspace.py verify` | PASS: drift, traceability, delivery plan, Ruff, Mypy, backend 99 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC does not migrate Provider consumers from the existing environment compatibility path, add
OS keychain storage, or build GUI settings screens. Those changes require separate migration,
desktop, or UI work. Existing identity migration and frontend jsdom warnings remain unrelated
repository conditions.

## Environment

- Time: 2026-07-17 17:05:03 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
