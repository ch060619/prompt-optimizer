# RC-177 Evidence

<!-- RC ID: RC-177. -->

## Delivered

- Unified both setup completion states on the existing `/workspace/home` route, preserving the optional workspace query and account type.
- Added shared workspace route helpers and a non-sensitive route catalog so API and local model choices survive switching and page reloads without recreating a project or session.
- Added a workspace model selector with offline, cloud Provider/model, and ready local model entries.
- Selecting a model updates only the workspace Provider/model route; API keys and account credentials are not copied into the selector or route catalog.
- Fixed the mobile workspace-home cascade so recent projects and tasks stack vertically and the status grid remains readable.

## Validation

- RC-177 focused tests: 14 passed across `WorkspaceHome`, `ProviderModels`, and `LocalModels`.
- Full frontend suite: 20 test files, 90 tests passed.
- ESLint, TypeScript, and Vite production build passed.
- API and local setup tests assert the same destination shape: `/workspace/home?workspace=<scope>`.
- Playwright desktop `1440x1100`: `scrollWidth === clientWidth === 1440`.
- Playwright mobile `390x844`: `scrollWidth === clientWidth === 375` (browser scrollbar excluded), with no horizontal overflow.
- Screenshots: `output/playwright/rc-177-workspace-desktop.png` and `output/playwright/rc-177-workspace-mobile.png`.
- Browser snapshot exposed `Offline Rules / offline`, `Cloud / openrouter / team/model-v1`, and `Local / gemma-3-4b`; switching to local persisted the local route while retaining both catalog entries.

## Limits

- The page uses the existing guest/account distinction and localStorage route catalog; durable cross-device project/session synchronization remains backend work.
- The cloud entry is the configured non-secret Provider/model route; real Provider requests remain outside this Mock-first validation.
- Existing jsdom navigation warning remains in the frontend suite.
