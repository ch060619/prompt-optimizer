# RC-168 Evidence

<!-- RC ID: RC-168. -->

## Delivered

- Added `ModelDiscoveryService` for Provider Preset `/models` endpoints with
  cursor pagination, bounded page traversal, injected HTTP clients, and TTL
  caching.
- Classified unauthorized, forbidden, rate-limit, server, timeout, network,
  invalid-response, and unsupported discovery outcomes without exposing
  credentials or remote response bodies.
- Registry discovery reuses the configured Provider endpoint and Preset
  defaults. Cached remote models, saved models, and manual model IDs are
  merged without duplicates; failures never discard known choices.
- Model IDs use format/length/control-character validation only. No hard-coded
  model allowlist was introduced. The Provider UI applies the same manual-ID
  boundary and disables discovery until model-listing capability is known.

## Validation

- RC-160 through RC-168 Provider regression: 57 passed.
- RC-168 discovery contract: 4 passed, covering paginated success, cache hit,
  empty list, timeout, 403, saved/manual retention, validation, and Registry
  Preset endpoint selection.
- Frontend full suite: 20 test files, 87 passed; Provider UI suite: 5 passed;
  ESLint and `tsc --noEmit`: PASS.
- Provider Ruff and Mypy: PASS.

## Limits

- No real Provider request was made and no external service charge was
  incurred.
- Real connection testing, user confirmation, cost warning, and token limits
  remain in RC-169.
- The full frontend suite, ESLint, and the production Vite build pass in the
  project workspace.
