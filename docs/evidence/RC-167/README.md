# RC-167 Evidence

<!-- RC ID: RC-167. -->

## Delivered

- Added the versioned `v1` capability snapshot schema with static adapter
  declarations, probe source, observation/expiry timestamps, and safe probe
  error metadata.
- Added `ProviderCapabilityResolver` with provider/model keyed TTL caching,
  forced refresh, probe aliases such as `tool_use` and `vision`, and static
  fallback when a probe fails.
- Added an explicit capability matrix for Chat Completions, Responses,
  Gemini, Anthropic, Azure, Vertex, Bedrock, offline, and local routes.
- Agent Core now negotiates optional tools and required structured output before
  opening a Provider stream. The Provider page gates model discovery on the
  declared or successfully probed `MODEL LISTING` capability.

## Validation

- RC-160 through RC-167 Provider regression: 53 passed.
- RC-167 capability, Agent gating, RC-078 negotiation, and Agent prototype
  regression: 12 passed.
- Provider Ruff and Mypy, Agent Mypy with `MYPYPATH=backend/src`, and Python
  compilation: PASS.
- Frontend full suite: 20 test files, 86 passed; Provider capability suite:
  4 passed; ESLint and `tsc --noEmit`: PASS.

## Full-suite limits

- The previously recorded OpenAPI, RC-141, RC-143, traceability, V2 baseline,
  and Windows SQLite cleanup failures have been fixed and are covered by the
  current full-workspace validation.
- No real paid Provider request was made and no external service charge was
  incurred.
- The full frontend suite, ESLint, and the production Vite build pass.
