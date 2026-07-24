# RC-217 Evidence

## Scope

Each of the 11 OpenAI-compatible Provider Presets now carries versioned
`rc217-v1` privacy metadata: fields sent, local/cloud location, service-region
qualification, an official policy URL, and an explicit retention-risk warning.
`GET /api/v1/provider-privacy` exposes only this public catalog. The Provider
configuration page and first-use API wizard show the selected notice before
the route is used. A custom endpoint has no inferred policy and is labeled
`CUSTOM ENDPOINT / USER RESPONSIBILITY`.

## Verification

- `backend/tests/test_rc217_provider_privacy.py`: 2 passed.
- Related RC-166, RC-216, API contract, and API regression tests: 49 passed.
- `scripts/check_provider_privacy.py`: 11 presets valid; official HTTPS host
  allowlist passed.
- HTTP spot checks for all 11 policy URLs returned 200, including the
  DeepSeek official URL discovered from its homepage and the Volcengine URL
  after a longer timeout.
- Frontend: 22 test files, 105 passed; ESLint, TypeScript, and Vite build
  passed.
- Strict Mypy, OpenAPI/client drift, traceability, and `scripts/workspace.py
  check` passed.

## Residual limits

Retention, training use, deletion controls, and actual service routing can
change by Provider policy, account, region, or custom endpoint. The catalog
does not make privacy guarantees and no real Provider request was sent.
