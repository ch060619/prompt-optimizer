# RC-179 Evidence

<!-- RC ID: RC-179. -->

## Delivered

- Added a `SecretStore` protocol with opaque `secret://rabbit-code/<id>` references, deterministic in-memory backend, unavailable fail-closed backend, and platform selection.
- Added Windows Credential Manager storage through `Advapi32` `CredWriteW`/`CredReadW`/`CredDeleteW`.
- Added Linux Secret Service integration through `secret-tool` with argv-only lookup/clear and secret input on stdin; no shell interpolation is used.
- Updated `ConfigService` so user-layer `api_key` values must be opaque references and are resolved only through the SecretStore; plaintext user configuration is rejected.
- Added atomic config writes, secret replacement cleanup, secret deletion, masked display, and transient session/CLI `api_key` values that are never persisted.

## Validation

- RC-179 SecretStore/ConfigService tests: 5 passed.
- Existing RC-064 storage boundary, RC-179, and Provider regression tests: 18 passed.
- Ruff, targeted Mypy, Python compileall, and sensitive implementation scan passed.
- Windows Credential Manager temporary put/get/delete round-trip passed and the generated credential was deleted in teardown.
- No API key was written to the test config JSON; the stored value was an opaque reference.

## Limits

- The current host is Windows; Linux Secret Service was implemented but not claimed as a Linux machine test because `secret-tool`/a Linux desktop session is unavailable here.
- The unavailable backend deliberately rejects persistent credentials; session/CLI values remain the supported temporary fallback.
- Full cross-platform installer and OS integration validation remain environment-dependent.
