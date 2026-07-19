# RC-199 Evidence

## Scope

Implemented a user-scoped installation policy. Default model storage resolves from `RABBIT_CODE_HOME`, Windows user app data, or `XDG_DATA_HOME`; the model root is `local-models` below that directory and the user bin location is tracked separately. Directory creation checks ancestor write bits and a real write probe. The local installer now defaults to this model root when `--root` is omitted and rejects unwritable destinations without attempting elevation.

Elevation is represented only as an explicit, unconfirmed request containing the command, reason, and manual alternative. Confirmation is required before such a request can proceed. The PowerShell and POSIX wrappers remain thin user-process launchers and contain no elevation invocation.

## Verification

- `python -m pytest backend/tests/test_rc199_install_permissions.py -q`: 5 passed.
- RC-185/RC-191/RC-199 install regression: 14 passed.
- New install policy and CLI Ruff: passed.
- Strict Mypy for the policy and CLI: passed.
- Python compileall for the policy and CLI: passed.
- Wrapper scan: PowerShell `RunAs` absent; POSIX elevation command absent.

The CLI test runs `status` without `--root` under an isolated `RABBIT_CODE_HOME`, confirming the user model root is created and used. Permission tests cover a read-only system-like parent, explicit confirmation refusal, and a user-writable Windows-style path.

## Residual limits

No real standard-account installer session was run against an external protected system directory, and no OS package manager or runner binary was elevated. The intended behavior is fail-closed with a manual alternative; real installer packaging and platform-specific PATH persistence remain release-stage work.
