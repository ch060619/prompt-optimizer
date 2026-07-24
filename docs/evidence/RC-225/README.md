# RC-225 Evidence

<!-- RC ID: RC-225 -->

## Scope

Added restart reconciliation for the durable runtime surfaces available in
the repository:

- App Server startup marks queued/running SQLite tasks as failed with a
  retryable message while preserving their saved input.
- Local model lifecycle reads recover transient busy/loading/stopping states
  from the recorded installed file without treating an installed model as
  ready when the file is missing.
- `ProcessManager` atomically persists process records. A new manager
  reconciles stale running records as failed and keeps their cursor-readable
  log files.

## Verification

- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc225_recovery.py backend/tests/test_rc194_local_model_state.py backend/tests/test_rc198_runner_gateway.py backend/tests/test_rc094_process_tools.py backend/tests/test_api.py backend/tests/test_api_contract.py -q`: 41 passed.
- Targeted Ruff check: passed.
- Full backend strict Mypy: 138 source files passed.
- FastAPI startup reconciliation uses the supported lifespan API; the RC-225
  recovery test and API regression pass without the framework startup-hook
  deprecation warning.
- `scripts/workspace.py check` and generated API drift remain current after the
  RC-225 documentation/index update.

## Residual limits

Interrupted tasks are marked failed and retain their input for an explicit
retry; they are not silently re-executed. Real Ollama/llama.cpp processes,
cross-platform kill, and desktop-session crash injection remain platform test
conditions rather than silently simulated recovery results.
