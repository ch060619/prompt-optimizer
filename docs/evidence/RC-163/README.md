# RC-163 Evidence

<!-- RC ID: RC-163. -->

## Delivered

- `AnthropicMessagesAdapter` uses the Messages endpoint, `x-api-key`,
  `anthropic-version`, optional beta headers, `system` blocks, and content
  blocks instead of OpenAI message assumptions.
- Tool definitions are converted to Anthropic schemas; tool use responses and
  tool result inputs are preserved, with SSE text/tool events parsed.
- Usage is exposed from responses, prompt caching is opt-in, and
  `probe_capabilities()` reports tool use, caching, and beta extension support.

## Validation

- `backend/tests/test_rc163_anthropic.py` plus RC-160/161/162, Provider, and
  RC-151 regressions: 29 passed.
- Ruff and Mypy for the Provider adapters and RC-160 through RC-163 tests:
  PASS.

## Limits

- Validation uses deterministic `httpx.MockTransport` contracts; no real
  provider request or charge was made.
