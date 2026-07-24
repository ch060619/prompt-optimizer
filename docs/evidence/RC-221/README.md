# RC-221 Evidence

## Scope

Added the versioned `rc221-v1` portable contract in
`prompt_optimizer.export.portable`. JSON is canonical. ZIP contains only a
root `manifest.json` and `data.json`; the manifest binds the data size and
SHA-256. The document carries workspace identity, sessions with messages,
Prompt versions, templates, and an allowlist of non-sensitive settings.

Export omits Provider credentials, keychain references, authorization data,
passwords, tokens, and unknown settings. Import validates the Pydantic schema,
UTF-8/size limits, duplicate IDs, sensitive field names, ZIP root paths,
symlinks, duplicate entries, and manifest hash before returning data. Preview
reports counts and entity conflicts; the caller chooses `skip` or `replace`
before applying anything to storage.

## Verification

- `python -m pytest backend/tests/test_rc221_portable.py backend/tests/test_storage_export.py backend/tests/test_rc086_sessions.py backend/tests/test_rc089_session_database.py -q`: 16 passed.
- `python -m compileall -q` for the portable service and tests: passed.
- `python -m ruff check` for the portable service and tests: passed.
- `python -m mypy backend/src/prompt_optimizer/export/portable.py`: passed.
- Current full backend baseline: 646 passed, 9 skipped, 2 deprecation warnings.
  The generated reverse index is current and the earlier configuration,
  RC-141/RC-143, and V2 baseline/environment failures are resolved.

The focused tests cover clean JSON round-trip, ZIP round-trip, conflict
preview, skip behavior for sessions/prompts/messages/settings, credential
exclusion, duplicate IDs, schema rejection, and ZIP path traversal rejection.

## Residual limits

The service returns a validated document instead of mutating SQLite. A caller
must apply the chosen preview strategy to its repository. No real cross-version
desktop Profile migration was run; the current storage does not expose one
unified session/message repository to mutate safely, so that integration is
left explicit rather than hidden behind an unsafe partial write.
