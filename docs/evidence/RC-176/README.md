# RC-176 Evidence

<!-- RC ID: RC-176. -->

## Delivered

- Added the no-API setup route at `/workspace/models?entry=local` with ordered hardware, runner, model, license, install, and health phases.
- Added Ollama and `llama.cpp` runner choices plus Gemma 3 4B and Qwen2.5-Coder 7B model choices.
- Required license acceptance before download and exposed disk, CPU, GPU, and offline-readiness checks before setup continues.
- Added resumable local progress state in workspace-scoped `localStorage`, including start, pause, resume, cancel, checksum verification, and health completion states.
- Persisted only the selected local Provider route after the health check passes; no remote Provider request is made by this flow.

## Validation

- RC-176 focused frontend tests: 7 passed.
- Full frontend suite: 20 test files, 89 tests passed.
- ESLint, TypeScript, and Vite production build passed.
- Playwright desktop `1440x1100` and mobile `390x844` checks passed; mobile `scrollWidth === clientWidth` with no horizontal overflow.
- Mobile full-page screenshot: `output/playwright/rc-176-local-mobile.png`.
- Browser visual review confirmed the mobile wizard header, phase tracker, hardware facts, primary action, and saved-progress footer do not overlap or clip.

## Limits

- The runner/download lifecycle is a deterministic frontend flow; real Ollama or `llama.cpp` process loading and multi-gigabyte transfer remain runtime integration work for later RC items.
- Browser validation used the frontend dev server without a backend process; the existing health proxy unavailable state remains visible elsewhere in the app.
- Existing jsdom navigation warning remains in the frontend suite.
