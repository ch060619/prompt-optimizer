# RC-197 Evidence

## Scope

Implemented a registered local-model directory lifecycle:

- directory selection checks writability and free space;
- updates copy and SHA-256 verify a pinned version before activation;
- migration stages copies, verifies every registered file, switches the registry atomically, then removes only registered files from the old root;
- interrupted migration leaves the current root complete and usable;
- rollback selects a verified retained version;
- repair can re-install the active version from a verified source or select another complete retained version;
- cleanup prunes only registered non-active versions;
- uninstall removes only registered model files and preserves unrelated files and prompt history boundaries.

## Verification

- `python -m pytest backend/tests/test_rc197_model_lifecycle.py -q`: 6 passed, 4 existing path-migration warnings.
- RC-197 association regression (`RC-185`, `RC-191`, `RC-193` through `RC-197`): 28 passed, 5 existing warnings.
- Frontend full suite: 22 test files, 102 passed.
- `python -m ruff check` for RC-197 backend files: passed.
- Strict Mypy for touched backend modules: passed.
- `python scripts/generate_api.py --check`: passed.
- Frontend ESLint and TypeScript/Vite build: passed.
- `python scripts/workspace.py check`: passed.

The FastAPI contract test exercises directory check, version registration, migration, and registered uninstall. The migration interruption test confirms the source model remains complete until the verified destination is switched.

## Residual limits

Real Ollama/llama.cpp processes, model weights, GPU hardware, and cross-process filesystem fault injection were not run. Existing path migration warnings remain non-blocking. The earlier Ruff import-order and frontend jsdom navigation issues have been fixed; full-workspace Ruff, frontend tests, and the production build now pass.
