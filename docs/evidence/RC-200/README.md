# RC-200 Evidence

## Scope

Added a deterministic offline package layout:

```text
package/
  manifest.yml
  dependencies/
  models/<model-id-with-slashes-replaced>.<quantization>
```

`OfflineModelImporter` validates the controlled manifest, exact model ID, pinned revision, license confirmation, dependency and model directories, required free disk space, and SHA-256 before creating the target state. It then reuses `LocalInstallCore` for atomic local installation and `run_health_check` for the same runner version/load/generation/stream/cancellation/context/stop-reload/resource contract. The CLI is `scripts/import-local-model.py` and emits JSON only.

## Verification

- `python -m pytest backend/tests/test_rc200_offline_import.py -q`: 4 passed.
- RC-185/RC-188/RC-191/RC-192/RC-193/RC-200 association: 20 passed.
- Manifest validation and distribution weight scan: passed.
- Offline importer/CLI Ruff: passed.
- Strict Mypy for the importer and CLI: passed.
- Python compileall for the importer and CLI: passed.
- `python scripts/workspace.py check`: passed after traceability regeneration.

The tests cover successful no-network import, health report persistence, tampered model rejection before target creation, missing dependencies, license refusal, revision mismatch, insufficient disk, and CLI parity.

## Residual limits

No real offline VM, published dependency bundle, model weights, GPU, or real Ollama/llama.cpp import was run. The CLI uses an in-memory runner and an explicit deterministic resource probe for the contract test; production runner and package validation remain release-stage work.
