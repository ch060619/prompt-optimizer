# RC-208 Evidence

## Scope

Added a shared `TrustManifest` and `TrustRegistry` for plugins, skills, hooks,
MCP servers, and scripts. Manifests declare kind, source, semantic version,
SHA-256 artifact hash, and permissions. Registration requires explicit
confirmation; source, version, hash, or permission changes require
reapproval. Records support lock, unlock with confirmation, disable, enable,
revoke, and isolated execution context creation. The plugin registry also
rechecks the installed artifact hash before enable and execute, and disables a
plugin after tampering is detected.

## Verification

- `python -m pytest backend/tests/test_rc208_trust.py backend/tests/test_rc077_plugins.py backend/tests/test_rc099_extensions.py backend/tests/test_rc075_hooks.py backend/tests/test_rc076_mcp.py -q`: 25 passed.
- `python -m ruff check` for trust, plugin, extension, hook, MCP, and RC-208 test files: passed.
- `python -m mypy --strict --explicit-package-bases` for trust, plugin, and RC-208 test modules: passed.
- `python -m compileall -q` for trust, plugin, and RC-208 test modules: passed.

Tests cover explicit first approval, all supported manifest kinds, source and
permission allowlists, changed artifact reapproval, locked updates, disable
and revoke behavior, plugin runtime tamper detection, and isolated execution
context propagation.

## Residual limits

No real third-party extension process or credential access was executed. The
execution context is an application-level isolation boundary; OS-level sandbox
capability differences remain covered by RC-204 and future security testing.
Downloaded artifact HTTPS, license, and hash verification is tracked by
RC-209.
