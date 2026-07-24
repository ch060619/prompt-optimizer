# RC-224 Evidence

<!-- RC ID: RC-224 -->

## Scope

Added one shared `DataLimitDefaults` contract with positive-value and maximum
validation for tool output, context text, process logs, diffs, and
attachments. Text and captured output now expose `truncated`,
`original_bytes`, and `next_cursor`; process logs and diffs can be read from a
reported cursor. Attachments over the configured maximum are rejected instead
of being silently truncated.

## Verification

- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc224_limits.py backend/tests/test_rc082_context_items.py backend/tests/test_rc096_tool_results.py backend/tests/test_storage_export.py -q`: 14 passed.
- Targeted Ruff check: passed.
- Targeted strict Mypy check with `--follow-imports skip`: passed.
- `scripts/generate_api.py --check`: passed; generated OpenAPI and TypeScript artifacts are current.
- `scripts/workspace.py check`: passed after refreshing the generated RC reverse index.

## Residual limits

The shell capture and text context surfaces return bounded content plus a
continuation cursor; this change does not add a new persistent cross-request
output store or UI pagination. Process-log and Diff cursor reads are covered
by existing service contracts. Real million-byte/million-file pressure,
cross-platform process-memory, and desktop UI matrices were not available. The
RC-222 CLI, GUI HTTP harness, RSS, and backend-package probes now pass their
recorded budgets.
