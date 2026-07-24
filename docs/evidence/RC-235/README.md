# RC-235 Evidence

## Scope

Added `scripts/check_rc235_visual_regression.py` and
`frontend/tests/Rc235VisualRegression.test.tsx`. The gate checks the 14-route visual
manifest, light/dark 1x/2x PNG baselines, representative workflow screenshots, explicit
theme selection, decorative Rabbit artwork, and shared empty/error/offline/install states.

The committed baselines are the fixed-data `output/playwright/rc-133-*` matrix. The state
and workflow captures include `rc234-onboarding.png`, `rc234-workspace-home.png`, and
`rc234-send-after-adopt.png`.

## Verification

```text
python scripts/check_rc235_visual_regression.py
npm test -- --run tests/Rc235VisualRegression.test.tsx
npm run lint
.venv\Scripts\ruff.exe check scripts/check_rc235_visual_regression.py
```

Results: visual matrix gate passed; `17 passed`; ESLint and Ruff passed.

## Limits

This Windows session did not repeat every screenshot on a physical Linux desktop or a
native Tauri shell. The 56 baseline files are reused from the existing RC-133 fixed matrix;
unapproved pixel changes remain subject to the baseline review workflow.
