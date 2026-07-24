# Local Model Guide

Rabbit Code treats local inference as an optional runner. The release package contains no model weights. The CPU-only offline rules Provider is always the first fallback; a local model is used only after its runner is installed, healthy, and selected.

## Hardware planning

These are planning estimates, not performance guarantees. Quantization, context length, OS overhead, runner implementation, and concurrent tasks change the result.

| Model family | Typical role | Disk budget | RAM/VRAM planning |
| --- | --- | ---: | ---: |
| Gemma 2B/3B class | CPU smoke tests and short prompts | 3-6 GB | 8-12 GB system RAM |
| Gemma 7B/9B class | General local assistance | 6-12 GB | 16 GB system RAM or 8 GB VRAM plus system headroom |
| Qwen2.5-Coder 7B class | Code-focused local assistance | 6-12 GB | 16 GB system RAM or 8 GB VRAM plus system headroom |
| Qwen2.5-Coder 14B class | Larger code context | 12-24 GB | 32 GB system RAM or 16 GB VRAM plus system headroom |

Reserve extra space for a download temporary file, at least one previous version, runner cache, and the SQLite/log directories. Read the model card and license for the exact artifact before import.

## Supported local routes

- `ollama`: default endpoint `http://127.0.0.1:11434/v1`; the Ollama server must already be running.
- `lmstudio`: default endpoint `http://127.0.0.1:1234/v1`; load a model in LM Studio and enable its local server.
- `local`: the internal runner boundary used by the application and tests.

Check a configured route with:

```bash
rabbit doctor --json
rabbit path --json
rabbit optimize "Summarize this short note." --provider ollama --model <local-model-id>
```

The GUI route is `/workspace/models`; choose a model only when its lifecycle is `ready`. `not_installed`, `not_ready`, `out_of_memory`, and `timeout` states offer separate recovery actions.

## Online import

The repository provides a JSON-output installer core. It downloads only from a user-selected source, verifies SHA-256, records the license confirmation, and writes to a user-scoped model root.

PowerShell:

```powershell
.\scripts\install-local-model.ps1 start `
  --source C:\path\to\model.bin `
  --model-id qwen2.5-coder-7b `
  --runner ollama `
  --version 1 `
  --checksum <sha256> `
  --license-url <model-license-url> `
  --license-summary "Read the model card and license before import." `
  --license-confirmation-version 1 `
  --accept-license
```

Linux/macOS shell syntax is available in `scripts/install-local-model.sh`; macOS is not a supported release target even though the script uses portable shell syntax.

The command contract is implemented by `scripts/local_model_install.py` and supports `start`, `download`, `pause`, `resume`, `cancel`, `verify`, `install`, `run`, and `status`. Use `status` after an interrupted operation and resume only from the same user model root.

## Offline import

For a model already present on removable media, verify the checksum before handing it to the installer:

```powershell
Get-FileHash C:\path\to\model.bin -Algorithm SHA256
python scripts\local_model_install.py start `
  --source C:\path\to\model.bin `
  --model-id gemma-local `
  --runner ollama `
  --version imported-1 `
  --checksum <sha256> `
  --license-confirmation-version 1 `
  --license-url <model-license-url> `
  --license-summary "License reviewed for this import." `
  --accept-license
```

Do not bypass the checksum or copy a model directly into the registry. `ModelDirectoryService` keeps only registered, checksummed files and retains a bounded version history.

## Update, rollback, repair, and uninstall

An update writes a new version and keeps the configured retention count. If health checks fail, select the previous verified version or use the repair action. A corrupt checksum is a failed install, not a reason to continue loading the file.

The CLI uninstall command is for Rabbit Code application data:

```bash
rabbit uninstall --json
rabbit uninstall --purge-data --yes --json
```

The first command is a dry run. The second is destructive and requires explicit confirmation. Model-specific cleanup and rollback are exposed by the model lifecycle service/UI; keep the model license record when organizational policy requires an audit trail.

## Failure checklist

- `not_installed`: start or import the model and verify the runner endpoint.
- `not_ready`: start Ollama/LM Studio, load the model, and retry health discovery.
- `out_of_memory`: lower context/model size, stop other models, or use offline rules.
- `timeout`: check the runner log and retry once; do not create an unbounded retry loop.
- checksum failure: discard the artifact and obtain it again from the declared source.
- license failure: stop and record the exact model card/license version before retrying.
