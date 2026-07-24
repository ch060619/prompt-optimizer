# RC-265 Evidence

<!-- RC ID: RC-265 -->

## Scope

Added `docs/providers/local-models.md` covering Gemma and Qwen2.5-Coder hardware planning, Ollama/LM Studio routes, online/offline import, license confirmation, SHA-256 verification, user-scoped model directories, pause/resume/cancel, update/rollback/repair, cleanup, uninstall, and failure recovery.

## Verification

- `python scripts/check_docs.py --run`: passed.
- The installer command contract was checked against `scripts/local_model_install.py`, `scripts/install-local-model.ps1`, and `scripts/install-local-model.sh`.
- `examples/test_examples.py`: 3 passed; no model download or real runner is invoked.

## Limits

Hardware figures are explicitly planning estimates. Real GPU/CPU compatibility and model-license acceptance require a user-supplied environment and artifact; weights are not included in the repository.
