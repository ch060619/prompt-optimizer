# RC-173 Evidence

<!-- RC ID: RC-173. -->

## Delivered

- Added a shared MockTransport contract suite for OpenAI Chat Completions,
  OpenAI Responses, Gemini, Anthropic Messages, Azure OpenAI, Vertex AI, and
  Bedrock Converse.
- Included offline rules and local Runner providers in the shared
  `ModelProvider` behavior contract.
- Added a request recorder that redacts credential headers and asserts that
  mock snapshots contain no configured secret.
- Added a manual-only real Provider test. It requires an owned API key, an
  explicit enable flag, an explicit fee confirmation token, and a token limit;
  the default test path skips it without creating a network client request.
- Added a CI step that runs the Mock contract suite with real tests disabled.
  RC-169's connection tester remains the user-facing confirmation and cost
  warning boundary before a real request.

## Validation

- RC-173 contract and manual-gate tests: 15 passed, 2 skipped.
- RC-160 through RC-173 Provider/API regression: 107 passed, 2 skipped.
- Targeted Provider Ruff, Mypy, and full backend Python compilation passed.
- Traceability regression after index regeneration: 19 passed, 2 skipped.
- `scripts/workspace.py check` passed, including generated API drift,
  traceability, dependency boundaries, design tokens, route coverage, visual
  contract, and delivery plan checks.
- Frontend validation remained green: 20 test files, 87 tests, ESLint,
  TypeScript, and Vite build.

## Limits

- No real Provider request was made and no external service charge was
  incurred.
- The former RC-141 metadata substring false positive, RC-143 exception
  wrapping, RC-158 V2 evaluation fixture drift, traceability drift, and Windows
  cleanup-on-error failures have been corrected; the full suite is revalidated
  at the final integration gate.
- Full repository Ruff passes, including the RC-153 test and `rabbit_code`
  package import blocks.
