# RC-172 Evidence

<!-- RC ID: RC-172. -->

## Delivered

- Added persistent global and workspace model routes, plus session and
  optimizer-specific overrides, without storing credentials in route files.
- Added provider availability checks, fallback chain metadata, and offline
  fallback behavior for unavailable selected routes.
- Added request token/cost estimation from provider pricing and output reserve,
  with preflight budget rejection before a provider call.
- Exposed maximum token and cost limits through the service, API, CLI, stream,
  task, and optimization metadata paths.
- Fixed the compatibility `AppServices.optimize_and_save` wrapper to accept and
  forward both budget limits.

## Validation

- RC-160 through RC-172 Provider/API regression: 92 passed.
- RC-172 contract: 6 passed for route precedence and persistence, optimizer
  route isolation, unavailable-route fallback metadata, preflight budget
  rejection, token-limit reporting, and stream fallback metadata.
- Provider Ruff, targeted Provider/service/public Mypy with the repository
  `PYTHONPATH`, and full backend Python compilation passed.
- OpenAPI generation and drift check passed.
- Frontend ESLint passed; Vitest passed with 20 test files and 87 tests; Vite
  production build passed.

## Limits

- No real Provider request was made and no external service charge was
  incurred.
- Estimates are deterministic preflight estimates; provider-native usage and
  persistent budget accounting remain future work.
- The broader environment Mypy invocation still reports the existing untyped
  `rabbit_code.cli` and `rabbit_code.maintenance` imports; this RC used the
  targeted command above and did not change that unrelated boundary.
- Existing migration and jsdom navigation warnings remain recorded elsewhere.
