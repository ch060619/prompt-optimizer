# Docker Usage Policy

## Scope

Docker is **only** used for local development and testing of the Rabbit Code API. It is **not**:

- A production deployment method
- A substitute for desktop (Tauri) or CLI (pip) installation verification
- A way to deploy Rabbit Code as a public service

## What Docker Tests

The Docker container builds the frontend and serves the FastAPI backend on `127.0.0.1:8000`. The CI Docker job runs:

1. `docker build` — verifies the Dockerfile is valid
2. `docker compose up` — starts the API container
3. API smoke test — `GET /health` returns 200
4. `docker compose down` — clean teardown

## What Docker Does NOT Test

- Desktop installer (NSIS/MSI/deb/AppImage) — see `release.yml` `build-desktop` job
- CLI installation (pip install) — see `release.yml` `build-cli` job
- Tauri native binary — see `build_desktop.py`
- Clean environment install/uninstall — requires VM testing
- Code signing — explicitly excluded per project policy

## CI Separation

The CI workflow (`ci.yml`) maintains Docker and real-install tasks as **separate jobs**:

- `docker` job: Container build + API smoke test only
- `backend` job: Python tests, lint, type-check (no Docker dependency)
- `frontend` job: ESLint, Vite build, Vitest (no Docker dependency)

The release workflow (`release.yml`) builds real installers on native runners — never via Docker.

## Local Usage

```bash
# Start API for local development
docker compose -f docker-compose.dev.yml --profile dev up

# Run API smoke test
docker compose -f docker-compose.dev.yml --profile test up --abort-on-container-exit
```

The container binds to `127.0.0.1` only — it is not accessible from external networks.
