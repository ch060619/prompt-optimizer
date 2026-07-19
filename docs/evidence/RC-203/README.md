# RC-203 Evidence

## Scope

Added `AuthorizationStore` for explicit once, session, and structured rule
decisions on top of the RC-202 approval engine. Rules match exact tool and
workdir fields plus either exact/prefix command tuples and exact/within
normalized path fields; they do not parse arbitrary shell strings. Grants are
listed, revoked immediately, and session matching is isolated by session ID.
Editing denies the pending request and creates a new approval snapshot, while
the ToolRegistry reuses only a matching session grant.

## Verification

- `python -m pytest backend/tests/test_rc203_authorizations.py backend/tests/test_rc202_approval.py backend/tests/test_rc097_tool_registry.py -q`: 15 passed.
- RC-203 tests cover once-only approval, session scope, structured rule scope, deny with no executor, edit-to-new-snapshot, revoke, and ToolRegistry session reuse.
- `python -m ruff check` for authorization, registry, package exports, and RC-203 tests: passed.
- `python -m mypy --strict` for authorization and registry modules: passed.

## Residual limits

No persistent cross-process grant database, real OS sandbox, desktop process,
MCP server, or external network request was executed. The default GUI approval
surface still exposes only the explicit confirmation action; session/rule
management is an engine/API capability for the following integration work.
