# Provider Integration Guide

This guide covers the Provider adapters that exist in the repository. A connection test proves endpoint reachability and response shape; it does not prove that a Provider's retention, training, billing, region, or model license terms are acceptable for a particular prompt.

## Common configuration

Provider configuration is environment-based and uses the Provider name as an uppercase prefix. The canonical names are `OPENAI`, `GEMINI`, `ANTHROPIC`, `AZURE`, `VERTEX`, `BEDROCK`, and any OpenAI-compatible preset such as `OPENROUTER`. The registry also reads `*_BASE_URL`, `*_API_KEY`, `*_MODEL`, `*_API_PROTOCOL`, `*_API_VERSION`, `*_REGION`, `*_PROJECT_ID`, `*_DEPLOYMENT`, `*_PROXY_URL`, `*_NO_PROXY`, `*_CA_BUNDLE`, `*_HEADERS_JSON`, and the cost/timeout fields defined by `ProviderConfig`.

Use a process-scoped secret for a smoke test:

```powershell
$env:OPENAI_API_KEY = "replace-with-a-test-key"
$env:OPENAI_MODEL = "replace-with-a-model-id"
rabbit optimize "Return one sentence about testing." --provider openai --model $env:OPENAI_MODEL
```

```bash
export OPENAI_API_KEY="replace-with-a-test-key"
export OPENAI_MODEL="replace-with-a-model-id"
rabbit optimize "Return one sentence about testing." --provider openai --model "$OPENAI_MODEL"
```

Do not put a real key in a shell history, committed `.env` file, issue, test fixture, screenshot, or log. The GUI Provider form accepts a key once and keeps only an opaque credential reference in workspace state.

## Provider matrix

| Provider | Protocol | Required values | Endpoint notes |
| --- | --- | --- | --- |
| OpenAI | `chat_completions` or `responses` | `OPENAI_API_KEY`, `OPENAI_MODEL` | Set `OPENAI_API_PROTOCOL=responses` only for a Responses-compatible endpoint. |
| Gemini | `gemini` | `GEMINI_API_KEY`, `GEMINI_MODEL` | Uses native `generateContent` and `streamGenerateContent`. |
| Claude/Anthropic | `anthropic` | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | Uses the Messages API; set `ANTHROPIC_API_VERSION` and optional beta features explicitly. |
| Azure OpenAI | `azure_openai` | `AZURE_API_KEY`, `AZURE_BASE_URL`, `AZURE_DEPLOYMENT` | `AZURE_API_VERSION` is appended when the URL does not already contain it. |
| Vertex AI | `vertex` | `VERTEX_API_KEY`, `VERTEX_PROJECT_ID`, `VERTEX_MODEL`, `VERTEX_REGION` | Use a short-lived/bearer credential from the supported auth boundary. |
| Bedrock | `bedrock` | `BEDROCK_BASE_URL`, `BEDROCK_MODEL`, `BEDROCK_REGION` | Requires an official AWS SigV4 signer; a plain API key is not sufficient. |
| Custom OpenAI-compatible | `chat_completions` | `<NAME>_BASE_URL`, `<NAME>_API_KEY`, `<NAME>_MODEL` | Use a unique uppercase name and document its retention/region terms separately. |

The source of truth for endpoint defaults and privacy metadata is `backend/src/prompt_optimizer/providers/presets.py`. The source of truth for wire protocols is `backend/src/prompt_optimizer/providers/registry.py` and the adapter modules.

## Connection test and troubleshooting

1. Set the endpoint, model, and credential in the current process or GUI Provider setup.
2. Run `rabbit doctor --json` and inspect only the redacted report.
3. Use the GUI Provider/model page to discover models and run a connection test when the endpoint supports listing.
4. Run one short `rabbit optimize ... --provider <name>` request.

Common recovery:

| Error class | Check first | Do not do |
| --- | --- | --- |
| Auth | API key type, deployment, region, and account permission | Do not print the key to diagnose it. |
| Model | Exact model/deployment ID and region availability | Do not assume a model list is global. |
| Parameter | Context, tool, structured-output, and token limits | Do not silently remove safety or tool requirements. |
| Rate limit/balance | Account quota, retry-after, and configured budget | Do not loop indefinitely. |
| Network/timeout | Endpoint URL, proxy, CA bundle, IPv4/IPv6, and firewall | Do not switch to a different endpoint without documenting the data boundary. |
| Filter/region | Provider policy and account region | Do not describe a filtered request as a transport bug. |

The result metadata reports the selected Provider, model, local/cloud location, health, latency, fallback, and sanitized request ID. It must not include the credential value or full prompt body.

## Minimal adapter example

The following uses a fake transport in tests; it does not contact a Provider:

```python
from prompt_optimizer.providers import ModelRequest, OpenAICompatibleAdapter, ProviderConfig

config = ProviderConfig(
    name="example",
    base_url="https://example.invalid/v1",
    api_key="test-only",
    model="example-model",
)
adapter = OpenAICompatibleAdapter(config)
assert adapter.config.model == "example-model"
```

Real Provider tests belong in an explicitly enabled, secret-free manual environment. CI uses mock transports and the offline path.

## Data sending checklist

- Confirm the Provider, model, region, and retention policy before sending a sensitive prompt.
- Prefer `offline`, `ollama`, or `lmstudio` for content that must stay on the machine.
- Disable prompt history if the local database should not retain the input.
- Review the Provider privacy URL exposed by the preset and the current account terms.
- Delete shell history and rotate the key if it was pasted into a diagnostic command.
