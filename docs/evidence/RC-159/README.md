# RC-159 Evidence

<!-- RC ID: RC-159. -->

## Delivered

- The first-run API route is labeled `USE API / CONFIGURE PROVIDER` and says it
  is separate from a Rabbit Code account.
- Provider setup calls the credential a `PROVIDER API KEY` and explicitly states
  that it is not a Rabbit Code account password.
- The real Rabbit Code account route remains explicitly labeled `ACCOUNT LOGIN`.

## Validation

- `frontend/tests/ApiConfigurationLanguage.test.tsx`: 3 passed.
- Frontend ESLint: PASS.
- Frontend TypeScript: PASS.

## Environment Remediation

- The supported frontend-scoped Vitest command passes the full suite without
  scanning runtime artifacts, and Vite production build passes.
