# RC-207 Evidence

## Scope

Added an explicit strict local App Server boundary. Strict sidecar mode checks
the client and Host are loopback, accepts only the local Origin allowlist,
requires the per-startup startup token and protocol, rejects oversized request
bodies by both `Content-Length` and streamed byte count, and uses explicit CORS
methods/headers without wildcard origins.
Sidecar host configuration is loopback-only and startup tokens come from a
high-entropy generator; the strict boundary is enabled by the sidecar server.

## Verification

- `python -m pytest backend/tests/test_rc207_local_api_security.py -q`: 3 passed, including a chunked request without `Content-Length`.
- `python -m ruff check` for API, sidecar, and RC-207 test files: passed.
- `python -m mypy --strict` for API and sidecar modules: passed.

Tests cover high-entropy token generation, public health on loopback, bad Host,
bad Origin, missing token, declared and chunked oversized bodies, protocol
compatibility, and sidecar restart/new-port/new-token behavior.

## Residual limits

No external-machine network exposure test was performed. The strict ASGI
boundary now stops a streamed body as soon as its accumulated bytes exceed the
configured limit and buffers at most the allowed body size for downstream use.
