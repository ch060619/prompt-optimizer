# RC-175 Evidence

<!-- RC ID: RC-175. -->

## Delivered

- Added an API setup route at `/workspace/providers?entry=api` with four ordered
  steps: protocol/provider, endpoint/credential, model, and test/default.
- Added protocol choices for Chat Completions, Responses, Gemini native, and
  Anthropic Messages, plus common service presets and custom endpoint support.
- Added Base URL, provider API key, and model inputs with validation and a
  visible boundary that the key is not a Rabbit Code account password.
- Saved only protocol, service, Base URL, model, and current step to a
  workspace-scoped draft; API key state stays in memory and is absent from
  draft/default-route storage.
- Locked `SAVE AS DEFAULT` until the Mock `$0` connection test succeeds, then
  persisted the non-secret route and marked API setup complete.
- Expanded the frontend route reader to accept all supported Provider IDs,
  including `openrouter` and `deepseek`, after setup saves a default.

## Validation

- RC-175 wizard and related onboarding/provider tests: 9 passed.
- Full frontend suite: 20 test files, 88 tests passed.
- ESLint, TypeScript, and Vite production build passed.
- Playwright desktop `1440x1100` and mobile `390x844` checks passed; mobile
  `scrollWidth === clientWidth === 390` with no horizontal overflow.
- No real Provider request was made and no API key was persisted or sent by the
  wizard's Mock `$0` connection test.

## Limits

- The current setup test is deliberately Mock-first; OS SecretStore and
  official OAuth are later credential-boundary work in RC-179/RC-182.
- Browser validation used the frontend dev server without a backend process;
  the existing health proxy unavailable state remained visible.
- Existing jsdom navigation warning remains in the frontend suite.
