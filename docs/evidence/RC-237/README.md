# RC-237 Evidence

## Scope

Added `backend/tests/test_rc237_local_models.py`. It reads the pinned Gemma and
Qwen2.5-Coder manifest entries, uses a small temporary source file, and exercises the
Fake Runner lifecycle through pause/resume, checksum verification, health gating,
generation, and running. A second matrix covers corruption repair and uninstall history
preservation for both model IDs.

Existing RC-185/186/189/190/191/193/196/197 tests remain part of the combined local-model
verification and cover retry, hardware probes, family-specific smoke, health failure,
OOM recovery, and version lifecycle details.

## Verification

```text
python -m pytest backend/tests/test_rc237_local_models.py -q
python -m pytest backend/tests/test_rc237_local_models.py backend/tests/test_rc185_local_install.py backend/tests/test_rc189_qwen_model.py backend/tests/test_rc190_gemma_model.py backend/tests/test_rc193_health.py backend/tests/test_rc196_runner_resources.py backend/tests/test_rc197_model_lifecycle.py -q
.venv\Scripts\ruff.exe check backend/tests/test_rc237_local_models.py
```

Results: RC-237 `4 passed`; combined local-model selection `21 passed`; Ruff passed.

## Limits

No large model weights, real external runner, physical GPU, low-memory machine, or
cross-platform hardware was used. Those are explicitly retained as controlled platform
matrix work rather than represented as CI results.
