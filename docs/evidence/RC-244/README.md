# RC-244 Evidence

RC ID: RC-244

## Scope

`backend/rabbit_code/shared_surface.py` now carries a revisioned shared-workspace
snapshot, change events, Provider/model/permission state, prompt versions, file
change summaries, and explicit optimistic-lock conflicts. The GUI/CLI clients can
refresh the same serialized state without silently overwriting a newer revision.

## Verification

```text
.venv\\Scripts\\python.exe -m pytest backend/tests/test_rc244_cross_surface.py -q
```

Result: `2 passed`.

## Limits

The contract is verified with local temporary storage and deterministic clients;
no real desktop shell, terminal process, or external Provider was used.
