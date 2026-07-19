# RC-202 Evidence

## Scope

Implemented a one-shot `PermissionApprovalEngine` backed by the shared protocol
`ApprovalRequest` schema. Requests include the tool, exact command, normalized
paths, normalized workdir, impact, authorization scope, complete arguments, a
SHA-256 snapshot, and an expiry time. `ToolRegistry` now returns an approval
request before a dangerous handler can run and executes only an approved,
matching snapshot. GUI and TUI consume the same request fields.

## Verification

- `python -m pytest backend/tests/test_rc202_approval.py backend/tests/test_rc101_tui.py backend/tests/test_rc097_tool_registry.py backend/tests/test_rc201_capability_policy.py -q`: 23 passed.
- `python -m ruff check` for the changed approval, registry, TUI, protocol, and test files: passed.
- `python -m mypy --strict` for the changed approval, registry, and TUI modules: passed.
- `npm test -- --run tests/UiStates.test.tsx`: 8 passed.
- `npm run lint -- --quiet` and `npm run build`: passed.

The tests cover complete request snapshots, normalized paths, denial and
timeout with no executor call, one-shot consumption, parameter substitution
rejection, registry integration, shared TUI rendering, and GUI detail display.

## Residual limits

No real OS sandbox, desktop process, MCP server, or external network request
was executed. Existing platform-specific skips and the dirty, uncommitted
worktree remain as previously recorded; these are outside RC-202's contract.
