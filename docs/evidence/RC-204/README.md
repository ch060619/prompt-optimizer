# RC-204 Evidence

## Scope

Added `SandboxReport`/`SandboxController` with capability detection for Linux
bubblewrap, Windows Job Objects, AppContainer, ACL workspace controls, and the
existing workspace/symlink boundary. Linux bwrap launch specs isolate PID,
mount, IPC, UTS, and default network namespaces with read-only system mounts;
Windows reports Job Object support and explicitly records AppContainer/ACL
non-equivalence. Unavailable strong isolation fails closed, while reduced
execution requires explicit approval. `ProcessManager` checks the controller
before spawning.

## Verification

- `python -m pytest backend/tests/test_rc204_sandbox.py backend/tests/test_rc094_process_tools.py -q`: 9 passed, 1 skipped.
- `python -m ruff check` for sandbox, process boundary, and RC-204 tests: passed.
- `python -m mypy --strict` for sandbox and process boundary modules: passed.
- Simulated Windows/Linux reports cover capability differences; traversal and
  symlink fixtures are rejected; bwrap command construction and approved
  reduced process lifecycle are covered.

## Residual limits

No real Linux bwrap host, seccomp profile, AppContainer token, ACL policy, or
OS-level escape fixture was executed. The Windows test uses the existing local
Job Object-capable runtime and does not claim AppContainer or ACL equivalence.
