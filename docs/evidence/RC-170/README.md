# RC-170 Evidence

<!-- RC ID: RC-170. -->

## Delivered

- Added one canonical Provider error taxonomy: `auth`, `balance`,
  `rate_limit`, `region`, `model`, `parameter`, `filter`, `network`,
  `timeout`, `server`, and `cancelled`.
- Centralized HTTP status and error-body mapping for OpenAI-compatible,
  Responses, Gemini, Anthropic, Azure, Vertex, and Bedrock adapters.
- Preserved only validated, bounded Provider request IDs and exposed them as
  `provider_request_id`; API and stream error envelopes redact messages and
  never include credentials or prompt internals.
- Shared category presentation supplies canonical error codes, HTTP status,
  CLI exit codes, retryability, and recovery actions. The CLI and GUI consume
  the same presentation contract; the GUI routes recovery actions to Provider,
  model, network, diagnostics, or workspace surfaces.
- Regenerated the OpenAPI baseline and TypeScript client, including structured
  `ApiRequestError` fields for code, category, recovery action, exit code, and
  Provider request ID.

## Validation

- RC-160 through RC-170 Provider/API regression: 78 passed, 6 existing
  migration warnings.
- RC-170 contract: 18 passed across all HTTP categories, seven Adapter
  families, network/timeout/cancelled presentation, and request ID redaction.
- Frontend full suite: 20 test files, 87 passed; focused App/API suite: 18
  passed; ESLint and TypeScript/Vite build passed.
- OpenAPI generation drift check passed; Provider Ruff and Mypy passed with
  `PYTHONPATH=backend/src;backend;packages/protocol`; Python compilation passed.

## Limits

- No real Provider request was made and no external service charge was
  incurred.
- Existing jsdom navigation and data-directory migration warnings remain.
- The repository contains unrelated uncommitted work from earlier RC items;
  this evidence records the RC-170 delta without resetting it.
