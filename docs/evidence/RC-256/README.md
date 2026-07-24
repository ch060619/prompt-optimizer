# RC-256 Evidence

RC ID: RC-256

## Scope

Ran the frontend through the local Vite server with Playwright CLI at 1440 x
1100 and 390 x 844. The evidence covers the workspace and Change Review
surfaces, including screenshot capture, viewport dimensions, scroll width, key
layout rectangles, visible interactive controls, and console errors.

## Verification

- Workspace desktop: `scrollWidth=1440`, `scrollHeight=1100`; composer and
  primary controls stayed inside the viewport.
- Workspace mobile: `scrollWidth=390`, vertical scrolling was expected, and
  visible buttons stayed within the 390px content width.
- Change Review before the fix exposed a clipped mobile layout: the diff pane
  was only 40px wide and the review sidebar extended to `right=528`.
- Added a scoped compact override in `frontend/src/styles.css`.
- Change Review after the fix: at 390px the file tree, diff pane, and review
  sidebar each measured `x=0`, `right=390`; at 1440px the three columns ended
  at `right=1440`.
- Playwright console check: 0 errors, 0 warnings.
- Screenshots: `output/playwright/rc256/rc256-workspace-desktop.png`,
  `rc256-workspace-mobile.png`, `rc256-review-desktop.png`, and
  `rc256-review-mobile.png`.

## Residual limits

The prior RC-133 matrix remains the broad 14-route visual baseline. This item
adds current runtime evidence for the workspace and Review surfaces and fixes
the previously recorded compact Review layout issue; native Tauri and physical
device matrices remain platform work.
