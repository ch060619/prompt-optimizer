# RC-231 Evidence

## Scope

Added `backend/tests/test_rc231_provider_contracts.py` with one shared MockTransport
contract for OpenAI Chat Completions, OpenAI Responses, Gemini, Anthropic Messages, and
an OpenAI-compatible OpenRouter endpoint. The suite checks request shapes, tool calls,
stream event ordering, forward-compatible unknown fields, secret-free bodies, and common
authentication/parameter error mapping.

## Verification

```text
python -m pytest backend/tests/test_rc231_provider_contracts.py -q
.venv\Scripts\ruff.exe check backend/tests/test_rc231_provider_contracts.py
```

Result: `15 passed`.

Static check result: `All checks passed!`.

## Limits

All cases use `httpx.MockTransport`; no provider credentials or external network are used.
