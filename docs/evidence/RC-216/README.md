# RC-216 Evidence

## Scope

Added `ExecutionDestination` as the shared request destination model and
exposed it through `POST /api/v1/execution-destination`. Optimization metadata
now carries the execution location, destination service/host, and a privacy
notice. The Provider target host is derived from its configured base URL
without exposing credentials. The Composer displays the local/cloud target
before a request and updates it when the selected route changes.

## Verification

- `backend/tests/test_rc216_execution_destination.py`: 2 passed.
- API and related regression tests: 25 passed.
- Frontend: 22 test files, 104 passed; ESLint, TypeScript, and Vite build passed.
- OpenAPI/client/schema generated-file drift and `scripts/workspace.py check` passed.

## Residual limits

No real Provider request or external network call was made. Provider-specific
data transfer fields, official policy links, retention-risk wording, and
custom-endpoint responsibility are handled by RC-217. Cross-platform native UI
testing remains an environment-dependent follow-up.
