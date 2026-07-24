# RC-268 Evidence

<!-- RC ID: RC-268 -->

## Scope

Added `docs/security/privacy-and-data.md` and linked it from `SECURITY.md`. The documents cover supported versions, private vulnerability reporting, credential rotation, local/cloud data boundaries, telemetry consent/version and allow-listed fields, Provider limits, retention preview, application-data deletion, and external data that Rabbit Code cannot delete.

## Verification

- `python scripts/check_docs.py --run`: passed.
- `test_rc210_privacy.py`, `test_rc217_provider_privacy.py`, `test_rc218_retention.py`, and `test_rc220_telemetry.py`: 14 passed.
- Defaults were checked against `privacy.py`, `retention.py`, `frontend/src/settings.tsx`, and the Provider privacy metadata.

## Limits

Provider-side retention/training/deletion, external runner caches, OS backups, and shell history remain outside the application's deletion authority and are documented as such.
