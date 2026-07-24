# RC-263 Evidence

<!-- RC ID: RC-263 -->

## Scope

Added `docs/architecture/rabbit-code.md` with process/module/data-flow diagrams, the CLI/Web/Tauri request path, Agent loop and tool boundary, protocol/data contracts, Provider adapter boundary, local data and failure recovery, and desktop sidecar limits. Each boundary links to current source paths and ADRs.

## Verification

- `python scripts/check_docs.py --run`: passed.
- Architecture references the current `backend/rabbit_code`, `backend/src/prompt_optimizer`, `frontend`, and `apps/desktop/src-tauri` paths.

## Limits

The document describes the current shell boundary; it does not claim that Tauri bundling or native installers are enabled.
