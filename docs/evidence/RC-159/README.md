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

## Environment Note

- Running Vitest from the repository root is blocked by EPERM while scanning the
  existing `.runtime/pytest-rc154` directory. Running the same test from the
  `frontend` working directory passes.
