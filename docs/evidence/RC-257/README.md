# RC-257 Evidence

RC ID: RC-257

## Scope

Hardened the workspace Composer boundary between the secondary optimization
action and the primary send action.

## Changes and verification

- `frontend/src/App.tsx` now passes the real prompt draft to
  `PromptOptimizeButton`; an empty placeholder is no longer sent as input.
- App and component tests cover empty-input rejection, one active request,
  cancellation/duplicate-click protection, revision snapshots, late results,
  and editable preview adoption.
- Focused frontend verification: App and PromptOptimizeButton, 24 tests passed.
- `npm run lint` passed; `npm run build` passed.
- Playwright empty-state check: optimization and send were both disabled;
  star geometry was 42 x 42 with transparent background and send geometry was
  93 x 48; console errors/warnings were both zero.
- Screenshot: `output/playwright/rc256/rc257-workspace-empty.png`.

## Residual limits

The component-level cancel behavior intentionally treats a second click while
busy as cancellation, not a second request. Real Provider calls remain outside
CI and were not sent.
