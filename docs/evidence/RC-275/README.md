# RC-275: Local Model On-Demand Download

## Status

**Complete** — No model weights in build configs, on-demand download with checksum+retry verified.

## What Was Done

1. **Verification**: No model weight files (.gguf, .safetensors, .pt, .pth, .onnx, .tflite, .ckpt) exist in the source tree (excluding .venv/node_modules).

2. **Build config audit**:
   - `tauri.conf.json` — no model weight references
   - `sidecar.spec` — no model weight references
   - `build_desktop.py` — no model weight references
   - `build_reproducible.py` — no model weight references

3. **Existing on-demand download system** (`backend/src/prompt_optimizer/local_install.py`):
   - `InstallSnapshot` dataclass with checksum, source_path, installed_path fields
   - Install phases: download → verify → install → ready
   - Status tracking: idle, downloading, paused, cancelled, failed, health_check, ready, running
   - SHA-256 checksum verification via `hashlib`
   - Retry logic with configurable max_retries and backoff
   - License confirmation before download
   - Mirror and proxy support
   - RC-185 and RC-191 already implemented these features

4. **Validation script** (`scripts/check_rc275_model_download.py`):
   - Checks all build configs for model weight file extensions
   - Verifies local_install.py has checksum, hashlib, download, retry, failure handling
   - Scans source tree for model weight files

5. **Test** (`backend/tests/test_rc275_model_download.py`):
   - 9 tests, all pass

## Verification

- `python scripts/check_rc275_model_download.py` → PASS
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc275_model_download.py -q` → 9 passed
