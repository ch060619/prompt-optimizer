# RC-247 Evidence

RC ID: RC-247

## Scope

The local-model journey covers the no-API route, hardware check, Gemma setup,
Qwen setup, health verification, model selection, conversation, and FastAPI
optimization using the existing local setup state machine.

## Verification

```text
cd frontend
npm run test -- --run tests/CrossSurfaceJourneys.test.tsx
```

Result: `1 passed` for the Gemma and Qwen setup routes; the test asserts that no
network call is made during the mocked lifecycle.

## Limits

This does not download weights or claim a physical CPU/GPU lifecycle pass. Model
download, hardware, and platform execution remain release/platform evidence.
