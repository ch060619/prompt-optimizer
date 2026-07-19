# RC-178 Evidence

<!-- RC ID: RC-178. -->

## Delivered

- Persisted Provider configurations per workspace, including non-secret endpoint, model, capability, enabled, connection, and default state; API keys remain transient and are absent from the stored config.
- Provider CRUD now supports create, edit, enable/disable, model add/select/remove, and delete.
- Deleting a default or active Provider, or a Provider referenced by active-session metadata, requires choosing an enabled configured replacement; the route is migrated before deletion.
- Disabling retains the Provider and model configuration/history and marks the route unavailable; optimization falls back to offline instead of using a disabled route.
- Persisted local model lifecycle state per workspace and added local model enable/disable while retaining the installed model history.
- Added a workspace-scoped Settings entry linking to the same Provider/model CRUD surface used by the model selector.

## Validation

- Full frontend suite: 20 test files, 93 tests passed.
- RC-178 focused Provider/local model/Settings tests: 16 passed.
- ESLint, TypeScript, Vite production build, and `git diff --check` passed.
- Playwright Provider/model page desktop `1440x1100` and mobile `390x844` checks passed; mobile `scrollWidth === clientWidth === 375` with no horizontal overflow.
- Screenshots: `output/playwright/rc-178-providers-desktop.png` and `output/playwright/rc-178-providers-mobile.png`.

## Limits

- Provider secrets are intentionally not persisted here; OS SecretStore integration is RC-179.
- Active-session reference detection consumes the current workspace's local active-session count metadata; full cross-process session ownership remains later runtime work.
- Existing jsdom navigation warning remains in the frontend suite.
