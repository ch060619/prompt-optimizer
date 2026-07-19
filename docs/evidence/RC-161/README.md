# RC-161 Evidence

<!-- RC ID: RC-161. -->

## Delivered

- `OpenAIResponsesAdapter` is separate from Chat Completions and is selected
  only through explicit `api_protocol=responses` configuration.
- Responses requests use `instructions`, `input` content items, `text.format`,
  Responses tool shape, and `/responses`; Chat-only `messages` are absent.
- Responses output text, function calls, streaming text deltas, function-call
  completion events, and cancellation checks are covered by the adapter.

## Validation

- `backend/tests/test_rc161_openai_responses.py` plus the RC-160, Provider, and
  RC-151 regressions: 23 passed.
- Ruff and Mypy for the Provider adapters and RC-160/161 tests: PASS.

## Limits

- Validation uses deterministic `httpx.MockTransport` contracts; no real
  provider request or charge was made.
