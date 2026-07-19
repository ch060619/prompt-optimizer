# RC-165 Evidence

<!-- RC ID: RC-165. -->

## Delivered

- Azure OpenAI resolves resource/deployment/API-version endpoints and sends
  `api-key` without a Bearer header.
- Vertex AI resolves project/region/model endpoints and uses Bearer
  authentication with the native Gemini contents/parts payload.
- Bedrock Converse resolves region/model endpoints and requires an injected
  official AWS SigV4 signer before sending a request.
- Provider Registry selects each hosted adapter by provider name or explicit
  protocol; credentials and endpoint shapes do not share a silent assumption.

## Validation

- `backend/tests/test_rc165_hosted_providers.py` plus RC-160 through RC-164,
  Provider, and RC-151 regressions: 40 passed.
- Provider Ruff and Mypy: PASS.

## Limits

- No real Azure, Vertex, or Bedrock request was made and no cloud charge was
  incurred.
- Bedrock production requests require an official AWS SigV4 signer supplied by
  the runtime; the repository test injects a deterministic signer double.
