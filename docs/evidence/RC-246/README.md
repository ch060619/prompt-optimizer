# RC-246 Evidence

RC ID: RC-246

## Scope

The mocked frontend journey covers API entry, Provider configuration and check,
conversation, diamond-star optimization, same-Provider optimization, editable
adoption, and independent send. Requests are captured locally to prove the
optimization result does not auto-send.

## Verification

```text
cd frontend
npm run test -- --run tests/CrossSurfaceJourneys.test.tsx
```

Result: `1 passed` for the API journey.

## Limits

This is a Mock API journey and sends no real request or cost-bearing traffic.
Real credentials and external Provider behavior remain an explicitly controlled
manual matrix.
