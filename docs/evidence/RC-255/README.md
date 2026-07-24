# RC-255 Evidence

## Scope

Added `docs/design/rabbit-code-ux-high-fi.md` with explicit Desktop 1440 x
1100 and Compact 390 x 844 geometry, a 2x screenshot baseline, composer state
matrix, long Provider/model/error text rules, bilingual wrapping rules, and
light/dark Design Token alignment.

## Verification

- The geometry is mapped to the current `reference-workspace`, composer,
  Provider, local-model, and settings selectors in `frontend/src/styles.css`.
- `packages/ui/tokens.json` is the cited source for colors, spacing, focus,
  motion, icons, and Rabbit budgets.
- Runtime screenshots and DOM boundary checks are intentionally recorded under
  RC-256, so this item does not claim visual runtime success ahead of that test.

## Residual limits

The existing reference workspace keeps a small legacy palette in its scoped
CSS rules; the specification records the shared token contract for new/detail
surfaces rather than silently rewriting unrelated styles in this task.
