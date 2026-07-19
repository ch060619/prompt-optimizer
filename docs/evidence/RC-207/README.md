# RC-207 Evidence

## Scope

Added an explicit strict local App Server boundary. Strict sidecar mode checks
the client and Host are loopback, accepts only the local Origin allowlist,
requires the per-startup startup token and protocol, rejects oversized request
bodies, and uses explicit CORS methods/headers without wildcard origins.
Sidecar host configuration is loopback-only and startup tokens come from a
high-entropy generator; the strict boundary is enabled by the sidecar server.

## Verification

- `python -m pytest backend/tests/test_rc207_local_api_security.py backend/tests/test_rc058_app_server.py backend/tests/test_rc067_lifecycle.py -q`: 11 passed, 24 existing path-migration warnings.
- `python -m ruff check` for API, sidecar, and RC-207 test files: passed.
- `python -m mypy --strict` for API and sidecar modules: passed.

Tests cover high-entropy token generation, public health on loopback, bad Host,
bad Origin, missing token, oversized body, protocol compatibility, and sidecar
restart/new-port/new-token behavior.

## Residual limits

No real port scan or external network exposure test was performed. The body
limit is enforced from `Content-Length`; a future streaming upload boundary
should also cap chunked bodies before exposing upload routes.
