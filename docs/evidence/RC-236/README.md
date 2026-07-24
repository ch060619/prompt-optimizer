# RC-236 Evidence

## Scope

Added `axe-core` as a frontend development dependency and
`frontend/tests/Rc236Accessibility.test.tsx`. The test scans the workspace and settings
shells for critical/serious accessibility findings and checks the permission dialog's
modal semantics, description, and keyboard focus behavior.

Added `scripts/check_rc236_accessibility.py` to keep focus-visible, reduced-motion,
forced-colors, axe, and dialog semantics present in the repository contract.

## Verification

```text
npm test -- --run tests/Rc236Accessibility.test.tsx
python scripts/check_rc236_accessibility.py
npm run lint
.venv\Scripts\ruff.exe check scripts/check_rc236_accessibility.py
```

Results: `2 passed`; axe reported no critical/serious findings; all static checks passed.

## Manual Result And Limits

Keyboard focus and dialog semantics were verified in the Windows jsdom/browser workflow;
focus-visible, reduced-motion, and forced-colors rules are present. NVDA/VoiceOver and
physical contrast measurement were not available in this session and remain a release
platform handoff item.
