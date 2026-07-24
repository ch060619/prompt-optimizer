# RC-251 Evidence

RC ID: RC-251

## Scope

The route coverage and visual regression gates cover 14 independent frontend
routes. Playwright produced 28 screenshots in `output/playwright/rc251`, one
desktop and one compact viewport per route, and the home/workspace screenshots
were manually inspected for RabbitMark visibility and content obstruction.

## Verification

```text
python scripts/check_rabbit_coverage_matrix.py --check
python scripts/check_rabbit_visual_regression.py --check
```

Both gates passed: `14 routes` and `14 routes x 4 baselines`.

## Limits

The manual inspection was a focused local review, not an external design sign-off;
native Tauri and physical-device matrices remain separate platform evidence.
