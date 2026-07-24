# RC-232 Evidence

## Scope

Added `backend/tests/test_rc232_fastapi.py` and a versioned WebSocket optimization route.
The suite covers startup token, loopback Origin/body boundaries, SSE replay, WebSocket
event ordering and invalid payload errors, offline fallback, authenticated background
tasks, and local runner route protection.

## Verification

```text
python -m pytest backend/tests/test_rc232_fastapi.py -q
.venv\Scripts\ruff.exe check backend/src/prompt_optimizer/api/app.py backend/tests/test_rc232_fastapi.py
```

Result: `8 passed`, with one pre-existing data-directory migration `DeprecationWarning`.

Static check result: `All checks passed!`.

## Limits

The provider and runner paths use in-process fakes or the offline provider. No real API,
runner process, external network, or production WebSocket client is used.
