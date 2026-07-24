# RC-222 Evidence

## Scope

Added `scripts/performance_baseline.py` and the versioned report
`docs/performance/baseline.json`. The script fixes the fixture, warm-up count,
iteration count, p50/p95 calculation, thresholds, and environment metadata.
It measures the real CLI `analyze` subprocess, offline first Token, indexed
search, Prompt diff, frontend dist size, frontend GUI cold/hot startup, process
RSS, and a locally built backend wheel.

## Verification

- Baseline command with 25 iterations completed and wrote `docs/performance/baseline.json`.
- CLI first response: p50 362.884 ms, p95 686.935 ms, budget 1000 ms: passed.
- Offline first Token: p50 0.158 ms, p95 0.189 ms, budget 1500 ms: passed.
- Search: p50 0.017 ms, p95 0.018 ms, budget 50 ms: passed.
- Diff: p50 0.009 ms, p95 0.016 ms, budget 50 ms: passed.
- Frontend dist: 916,908 bytes, budget 2,000,000 bytes: passed.
- GUI cold/hot p95: 1,549.399/26.139 ms, budgets 3,000/500 ms: passed.
- RSS: 28,962,816 bytes, budget 512,000,000 bytes: passed.
- Backend wheel: 288,943 bytes, budget 5,000,000 bytes: passed.
- Baseline `--check`, Ruff, and strict Mypy: passed.

## Residual limits

The GUI probe measures the built frontend through a local HTTP harness and
does not claim native Tauri startup. Native release packaging and the
cross-platform desktop matrix remain separate platform verification work, not
blocked or fabricated values in this web GUI baseline.
