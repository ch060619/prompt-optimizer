# RC-264 Evidence

<!-- RC ID: RC-264 -->

## Scope

Added `docs/providers/provider-integration.md` covering OpenAI, Gemini, Claude/Anthropic, Azure OpenAI, Vertex AI, Bedrock Converse, OpenAI-compatible custom endpoints, credentials, endpoints, model discovery, connection testing, data sending, errors, recovery, and a fake-transport adapter example.

## Verification

- `python scripts/check_docs.py --run`: passed.
- Provider names/protocols were checked against `providers/registry.py`, adapter modules, `ProviderConfig`, and `providers/presets.py`.
- The guide explicitly separates mock/secret-free CI checks from real credential and account verification.

## Limits

Provider retention, billing, region, model availability, and license terms remain external account responsibilities and are not asserted as verified by this repository.
