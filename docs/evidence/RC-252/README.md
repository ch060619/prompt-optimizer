# RC-252 Evidence

RC ID: RC-252

## Scope

`frontend/src/i18n.ts` provides typed English and Simplified Chinese catalogs,
locale switching, date/number formatting, and plural formatting. Settings uses
the resource layer and changes language immediately without changing the default
English compatibility behavior.

## Verification

```text
cd frontend
npm run test -- --run tests/I18n.test.ts tests/Settings.test.tsx tests/Onboarding.test.tsx
npm run lint
npm run build
```

The final focused combination passed `15` tests across five files; lint and build
also passed.

## Limits

This pass localizes the Settings/navigation surface and establishes the typed
catalog. A full static extraction of every legacy visible string remains a
follow-up before claiming complete key coverage.
