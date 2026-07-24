# RC-259 Evidence

## Scope

Added the motion budget at `docs/design/rabbit-motion-budget.md` and tightened
`frontend/src/components/SiteShell.tsx` so scroll animation setup is demand
driven and visibility-aware.

## Verification

- Work surfaces without `.reveal-on-scroll` do not create Lenis or a RAF loop.
- `prefers-reduced-motion: reduce` returns before animation setup.
- A hidden document cancels the active RAF; a visible document starts it again.
- Focused frontend verification: SiteShellMotion 3 passed, RabbitRoutes 9
  passed, App 17 passed, 29 tests total.
- `npm run lint` passed; `npm run build` passed.
- CSS reduced-motion rules keep scroll behavior automatic, transitions near zero,
  view transitions disabled, and reveal content visible/static.

## Residual limits

No long-duration CPU/GPU profiler was available in this local browser session;
the implementation and tests enforce lifecycle boundaries, while native desktop
resource profiling remains a platform/release check.
