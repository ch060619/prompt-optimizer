# RC-267 Evidence

<!-- RC ID: RC-267 -->

## Scope

Added `docs/development-guide.md` with fixed Python/Node/OS targets, installation, local servers, Docker boundary, unified workspace tasks, backend/frontend test matrix, generated API/data-model checks, debugging/diagnostics, SQL migrations, desktop shell checks, performance gates, release evidence, and platform limitations.

## Verification

- `python scripts/check_docs.py --run`: passed.
- `python scripts/generate_api.py --check`: passed; generated API artifacts are up to date.
- `python scripts/generate_data_model.py --check`: passed; data-model artifacts are current.
- `python scripts/workspace.py` prints the centralized task choices: install, generate-api, check, test, build, lint, typecheck, verify.

## Limits

Native installers and clean-machine installation are deliberately described as release evidence requirements; the current Tauri bundler is disabled and no platform pass is fabricated here.
