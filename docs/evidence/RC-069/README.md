# RC-069 Execution Evidence

- RC ID: RC-069
- Status: PASS for the local Agent CLI execution modes
- Owner: Codex
- Implementation commit: uncommitted working tree (HEAD `5610c00`)
- Scope: Support `rabbit` and `rabbit run`, one-shot and stdin execution, interactive TTY input,
  text/JSON/JSONL output, shared Runtime selection, and stable usage/runtime/cancel exit codes.

## Delivered

- Extended the Agent CLI parser with root and `run` forms, optional prompt input, stdin fallback,
  `--runtime`, `--output text/json/jsonl`, App Server options, and machine-safe output.
- Added interactive TTY input without Rich/ANSI output in machine modes; non-TTY input is consumed
  as a single prompt for pipeline use.
- Added stable exit codes: `0` success, `1` runtime/failure, `2` usage, and `130` cancellation.
- Added the production Typer `rabbit run` command that reuses the shared Agent Runtime executor.
- Added JSON snapshot, JSONL stream, text, TTY, stdin, failure/cancel, legacy compatibility, and
  production command tests.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest -q backend/tests/test_rc069_cli_modes.py` | PASS: 6 passed |
| `python -m pytest -q backend/tests/test_rc069_cli_modes.py backend/tests/test_rc057_agent_prototype.py backend/tests/test_cli_compatibility.py` | PASS: 12 passed |
| `python -m ruff check backend scripts` | PASS |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS: 52 source files |
| `python scripts/workspace.py verify` | PASS: drift, traceability, dependency boundaries, delivery plan, Ruff, Mypy, backend 120 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC covers the local Python Agent Runtime and CLI surfaces. Full TTY rendering, rich terminal
UX, JSON schema versioning across external clients, and the broader session/permission workflows
remain later Agent Core RCs. Existing path-migration DeprecationWarnings and the frontend jsdom
navigation warning remain unchanged.

## Environment

- Time: 2026-07-17 17:50:22 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
