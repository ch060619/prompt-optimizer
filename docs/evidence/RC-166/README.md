# RC-166 Evidence

<!-- RC ID: RC-166. -->

## Delivered

- Added a data-driven Provider Preset catalog for OpenRouter, DeepSeek,
  Moonshot/Kimi, Qwen, Doubao, Zhipu, SiliconFlow, Groq, Together, Ollama,
  and LM Studio.
- Each preset declares a display name, default Base URL, model discovery path,
  compatibility level, known limitations, and sensitive header names.
- Registry configuration uses preset defaults, supports explicit environment
  overrides, and parses `RABBIT_CODE_<NAME>_HEADERS_JSON` into custom headers.
- OpenAI-compatible requests apply custom headers while preserving the default
  authorization and content headers.

## Validation

- `backend/tests/test_rc160_openai_chat.py` through
  `backend/tests/test_rc166_provider_presets.py`: 48 passed.
- Provider Ruff: PASS.
- Provider Mypy: PASS.

## Limits

- No real paid Provider request was made and no external service charge was
  incurred.
- Ollama and LM Studio presets describe the local compatibility contract;
  model discovery and local service lifecycle are covered by RC-168 and later
  local-model work.
- The full frontend suite, ESLint, and the production Vite build pass in the
  project workspace.
