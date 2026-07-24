# RC-248 Evidence

RC ID: RC-248

## Scope

Offline rules remain available when a local model is not installed, not ready, or
fails with an out-of-memory condition. The response retains the original input,
includes fallback metadata and a repair/install action, and does not make an
external request.

## Verification

```text
.venv\\Scripts\\python.exe -m pytest backend/tests/test_rc248_fallback.py -q
```

Result: `3 passed`.

## Limits

The failure modes are deterministic injected states; no actual model process or
external network was used.
