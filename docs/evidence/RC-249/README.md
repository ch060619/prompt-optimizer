# RC-249 Evidence

RC ID: RC-249

## Scope

Composer drafts persist per workspace with revision, cursor, and attachment
references. A failed optimization restores the draft instead of clearing or
sending it, and the current revision remains the source of truth for retry.

## Verification

```text
cd frontend
npm run test -- --run tests/DraftProtection.test.tsx tests/App.test.tsx
```

Result: the focused draft/App combination passed; the final RC-244 to RC-253
regression run passed `15` tests across five files.

## Limits

Failure responses are mocked in CI. Real network outages, credentials, and model
process failures remain outside the deterministic frontend suite.
