# RC-258 Evidence

RC ID: RC-258

## Scope

Verified the Rabbit route slots against dense work information on Task,
Review, Terminal, Provider, local models, assets, settings, and diagnostics at
390 x 844.

## Verification

- Every checked work page used one decorative slot with `aria-hidden=true` and
  `pointer-events:none`.
- Mark slots measured 32 x 32 with opacity `0.16`; Terminal mono measured 32 x
  32 with opacity `0.12`; all slots ended at `right=378` inside the 390px
  viewport.
- Review, Terminal, Provider, Models, Assets, Settings, and Diagnostics had no
  interactive controls outside the viewport.
- Task initially inherited its later three-column base rule and pushed Task
  menu/inspector controls outside the viewport. Added a scoped compact stack in
  `frontend/src/styles.css`; after the fix Task controls ended at `right=373`
  or less and the shell measured `width=390`.
- Rabbit route, Task workspace, and Change Review tests: 15 passed.
- Playwright console check: 0 errors, 0 warnings.
- Screenshot: `output/playwright/rc256/rc258-task-mobile.png`.

## Residual limits

The RC-133 matrix remains the full 14-route light/dark baseline. This item
adds current dense-work mobile evidence; native Tauri, high-contrast hardware,
and physical-device checks remain platform work.
