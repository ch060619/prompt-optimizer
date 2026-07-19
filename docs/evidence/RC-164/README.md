# RC-164 Evidence

<!-- RC ID: RC-164. -->

## Delivered

- Added a local boundary parser that maps “Claude Code format” to the public
  Anthropic Messages API or an approved official Agent SDK integration.
- Only official `api_key` and `oauth` credential kinds are accepted.
- Cookie, subscription token, session token, internal token, unknown credential
  kinds, unknown protocol labels, reverse-engineered login, and Claude Code CLI
  distribution are explicitly rejected or prohibited.
- Provider UI copy states the same boundary without presenting subscription
  login as a supported route.

## Validation

- `backend/tests/test_rc164_claude_boundary.py`, Anthropic, and RC-151 tests:
  16 passed.
- Provider Ruff/Mypy: PASS.
- `frontend/tests/ProviderModels.test.tsx`: 3 passed; frontend ESLint and
  TypeScript: PASS.
- Existing RC-019/020/029 research boundary scripts remain the rights baseline.

## Limits

- No OAuth implementation or official Agent SDK integration is claimed here;
  those require separate provider approval and authorization conditions.
