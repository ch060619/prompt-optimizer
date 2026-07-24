# RC-280: Limit Docker Usage Scope

## Status

**Complete** — Dockerfile updated with dev/test-only comment, docker-compose.dev.yml created with 127.0.0.1 binding and dev/test profiles, CI has separate docker job, DOCKER.md policy document created, 22 tests passed.

## What Was Done

1. **Updated Dockerfile** — Added RC-280 comment: "Docker is for local development/testing of the API only. Do NOT use this image for production deployment or as a desktop/CLI substitute."

2. **Created `docker-compose.dev.yml`** — Dev/test only:
   - Binds to `127.0.0.1:8000` (not `0.0.0.0`)
   - Uses profiles (`dev`, `test`)
   - `restart: "no"` (no auto-restart)
   - Read-only data volume mount
   - Healthcheck for API

3. **Added Docker CI job** to `ci.yml` — Separate from backend/frontend jobs:
   - Builds Docker image
   - Starts container on 127.0.0.1
   - API smoke test (GET /health)
   - Non-root user verification
   - Clean teardown
   - Comment: "This does NOT replace desktop/CLI installation verification"

4. **Created `docs/DOCKER.md`** — Policy document:
   - Scope: dev/test only, NOT production
   - What Docker tests vs. does NOT test
   - CI separation explanation
   - Local usage instructions

5. **Created `scripts/check_rc280_docker_scope.py`** — 8 validation checks

6. **Created `backend/tests/test_rc280_docker_scope.py`** — 22 tests across 7 classes

## Verification Results

- `python scripts/check_rc280_docker_scope.py` → PASS
- `pytest backend/tests/test_rc280_docker_scope.py -q` → 22 passed

## Limitations

- Docker CI job runs on GitHub Actions (not local); local Docker Desktop not available in this session
- No production docker-compose.yml (by design — Docker is dev/test only)
- No Kubernetes/Helm deployment configs (by design — no public service)
