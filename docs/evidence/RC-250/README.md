# RC-250 Evidence

RC ID: RC-250

## Scope

Checkpoint snapshots cover multiple changed files, GUI/CLI diff views, accept or
reject decisions, restore, and concurrent user-edit conflicts. A stale revision
is rejected rather than replacing the user's newer file content.

## Verification

```text
.venv\\Scripts\\python.exe -m pytest backend/tests/test_rc250_cross_surface.py -q
```

Result: `1 passed` in the dedicated suite; the combined RC-244/245/248/250 run
passed `8` tests.

## Limits

The checkpoint contract uses temporary local workspaces. It does not claim a real
Git worktree or native desktop/CLI process matrix.
