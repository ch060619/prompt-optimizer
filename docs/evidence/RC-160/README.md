# RC-160 Evidence

<!-- RC ID: RC-160. -->

## Delivered

- The OpenAI-compatible adapter resolves a standard Base URL to
  `/chat/completions` while preserving an already complete endpoint.
- Requests include model, system/user messages, optional tool definitions and
  tool choice, plus `OpenAI-Organization` and `OpenAI-Project` headers.
- Non-streaming responses expose text and parsed function tool calls; SSE
  responses expose text deltas and tool-call deltas.
- 401/403, 429, and 408/504 responses map to unauthorized, rate-limit, and
  timeout provider errors. Keys and request bodies are not logged.

## Validation

- `backend/tests/test_rc160_openai_chat.py`, `backend/tests/test_providers.py`,
  and `backend/tests/test_rc151_routing_resilience.py`: 20 passed.
- Ruff and Mypy for the Provider adapter and RC-160 tests: PASS.

## Limits

- Validation uses deterministic `httpx.MockTransport` contracts; no real
  provider request or charge was made.
