# RC-174 Evidence

<!-- RC ID: RC-174. -->

## Delivered

- Kept the first-run page at two equal, unselected route choices: API/provider
  configuration and local model.
- Added direct decision information to both choices: data destination, network
  requirement, and provider-credential versus local-hardware boundary.
- Preserved keyboard-reachable links, explicit route URLs, and Rabbit Code
  artwork in the first viewport.
- Fixed the mobile CSS cascade so the onboarding hero switches to a block flow
  before the artwork; the previous desktop grid rule no longer collapses the
  copy column to 2px.

## Validation

- Onboarding and API-language frontend tests passed; full frontend suite passed
  with 20 test files and 87 tests.
- ESLint, TypeScript, and Vite production build passed.
- Playwright desktop viewport `1440x1100` verified equal two-column choices,
  visible Rabbit artwork, and complete route guidance.
- Playwright mobile viewport `390x844` verified the hero has no overlap and
  `scrollWidth === clientWidth === 390`; both choices are 342px wide and stack
  vertically.
- The page remained usable when the local API health proxy was unavailable; it
  showed the existing service-unavailable state and preserved both choices.

## Limits

- Browser validation used the frontend dev server without a backend process, so
  `/api/v1/health` displayed the expected unavailable state.
- Existing jsdom navigation warning remains in the frontend suite.
