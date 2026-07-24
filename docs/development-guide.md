# Development, Test, and Release Guide

## Fixed environment

- Python 3.12 or newer, managed with the repository virtual environment.
- Node.js 20.19 or newer; CI uses the latest Node 20 release.
- Frontend package manager: npm with `frontend/package-lock.json`.
- Release target: Windows 11 x64 and Ubuntu 24.04 x64. macOS is not a release target.
- Docker is a local development/test supplement, not desktop-install evidence.

## Install

```bash
python -m venv .venv
python -m pip install -e "backend[dev]"
python -m pip install -e packages/protocol
npm --prefix frontend install
```

The consolidated task wrapper is `python scripts/workspace.py`; it keeps install, check, test, build, lint, typecheck, and verify commands reproducible.

## Development servers

```bash
rabbit serve --host 127.0.0.1 --port 8000
npm --prefix frontend run dev
```

Vite serves the frontend on port 5173 and proxies API requests to the local FastAPI service. The production-like local flow is `npm --prefix frontend run build` followed by `rabbit serve`.

Docker development uses:

```bash
docker build -t rabbit-code:local .
docker run --rm --name rabbit-code-smoke -p 8000:8000 rabbit-code:local
```

## Checks and test matrix

```bash
python scripts/check_docs.py --run
python scripts/workspace.py check
python scripts/workspace.py lint
python scripts/workspace.py typecheck
python scripts/workspace.py test
python scripts/workspace.py build
python scripts/workspace.py verify
```

The backend matrix covers core rules, API contracts, storage/migrations, Provider mock transports, local model lifecycle, Agent Runtime, privacy/redaction, recovery, and performance gates. The frontend matrix covers route components, Provider/model settings, workspace controls, accessibility assertions, and production TypeScript/Vite build. Real cloud Provider calls and real model downloads remain manual tests with user-supplied credentials/artifacts.

Generated files must be checked after changing their source contracts:

```bash
python scripts/generate_api.py --check
python scripts/generate_data_model.py --check
```

## Debugging and migrations

Use `rabbit doctor --json`, `rabbit path --json`, and `/workspace/diagnostics` first. The output is redacted; do not add raw environment dumps to an issue.

Database schema changes are SQL migrations under `backend/migrations/`. Add a monotonically named migration, update the data-model source/fixtures when required, run the storage migration tests, and run `python scripts/generate_data_model.py --check`. Do not edit a user's SQLite file by hand during a bug report.

The source map is: `backend/src/prompt_optimizer/storage/migrations.py` applies migrations, `storage/service.py` owns transactions, and `scripts/backup_db.py`/`scripts/restore_db.py` cover backup recovery. Test both a fresh database and an upgrade from the previous fixture.

## Desktop shell

```bash
npm --prefix frontend run build
cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml
```

The Tauri shell is not the Agent or Provider layer. `apps/desktop/src-tauri/tauri.conf.json` currently has bundling disabled; installer generation and clean-machine installation are separate release tasks.

## Performance and release evidence

Generate performance data rather than typing a number into documentation:

```bash
python scripts/performance_baseline.py --iterations 25 --output performance-current.json --check
python benchmarks/performance_gate.py --baseline docs/performance/baseline.json --current performance-current.json --comparison-output performance-comparison.json --check
```

Release candidates must attach the test results, supported platform matrix, generated API/data model checks, dependency/security scans, SBOM, source/asset/license records, and known limitations. Stable release remains blocked until the release gate and packaging tasks have evidence.
