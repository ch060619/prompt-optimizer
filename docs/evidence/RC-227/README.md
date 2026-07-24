# RC-227 Evidence

<!-- RC ID: RC-227 -->

## Scope

Added bounded recovery diagnostics for the seven fault classes in the RC-227
matrix:

- Provider rate limits and network disconnects retry only through the configured
  finite `max_retries` boundary; terminal retryable failures update the circuit
  state instead of looping.
- Proxy transport failures are classified separately as `PROVIDER_PROXY` while
  retaining the shared network recovery action.
- Local model `MemoryError` preserves the request input, invokes the runner's
  OOM recovery hook, and reports `free_memory`.
- Model-directory disk exhaustion reports `DISK_FULL` before switching roots;
  SQLite lock/full errors expose bounded retry or disk recovery metadata.
- Process port checks expose `PORT_CONFLICT` and require selecting another port.

## Verification

- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc227_resilience.py backend/tests/test_rc197_model_lifecycle.py backend/tests/test_rc151_routing_resilience.py backend/tests/test_rc171_network_resilience.py backend/tests/test_rc225_recovery.py backend/tests/test_storage_backup.py -q`: 32 passed.
- Targeted Ruff check: passed.
- Strict Mypy for the changed Provider, SQLite error, and Storage modules: passed.
- `git diff --check`: passed.

## Residual limits

The fault matrix uses deterministic HTTP mock transports, an injected runner,
simulated disk usage, an actual temporary SQLite writer lock, and a local bound
socket. No real cloud outage, authenticated enterprise proxy, physical disk
exhaustion, cross-process SQLite crash, or desktop-native port allocation was
available; these remain manual/platform validation cases. Full-workspace Mypy
now passes with each package checked from its explicit source root; framework
and path warnings remain non-blocking.
