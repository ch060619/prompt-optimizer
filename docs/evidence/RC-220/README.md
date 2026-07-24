# RC-220 Evidence

## Scope

Telemetry remains closed by default. `TelemetryService.opt_in()` records the
versioned consent contract `rc220-v1`; the version is attached to each pending
event and can be serialized with the consent record. Events are limited to
anonymous technical metadata such as application version, event name,
duration, result, Provider/model identifiers, and resource counters. Prompt,
file, credential, request, and response content remains excluded unless the
existing separate content opt-in is explicitly selected.

Revocation immediately blocks new collection and sending. `clear()` removes
all pending local events. The Settings Privacy section stores the consent
version in workspace-local settings, documents the eligible local fields,
shows the off/consent state, and provides a separate action to delete the
workspace's pending telemetry key. No telemetry server, account, or remote
collector was added.

## Verification

- `python -m pytest backend/tests/test_rc210_privacy.py backend/tests/test_rc220_telemetry.py -q`: 8 passed.
- `python -m ruff check` for privacy and RC-210/RC-220 tests: passed.
- `python -m mypy backend/src/prompt_optimizer/privacy.py`: passed.
- `npm test` from `frontend`: 22 test files, 107 passed.
- `npm run lint` and `npm run build` from `frontend`: passed.

Negative coverage proves zero events by default, versioned opt-in, content
exclusion, immediate revoke behavior, queue deletion, and sender isolation.

## Residual limits

The repository intentionally has no telemetry backend. No real network send or
external account was used. The service sender remains an injected boundary for
an explicitly confirmed future/local transport; current Settings cleanup
removes the local pending queue key and does not claim remote deletion.
