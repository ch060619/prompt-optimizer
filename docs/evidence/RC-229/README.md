# RC-229 Evidence

<!-- RC ID: RC-229 -->

## Scope

Added a reproducible performance trend gate around the existing offline
baseline:

- The benchmark keeps the fixed prompt, 100-file search fixture, offline rule
  Provider, fixed diff versions, and frontend package measurement.
- Each current report records the Commit, machine, CPU/OS/runtime metadata and
  min/p50/p95/max statistics for measured latency metrics.
- `benchmarks/performance_gate.py` compares only metrics measured in both runs,
  applies an explicit noise ratio/absolute budget, preserves blocked probes as
  skipped, emits baseline/current statistics, and returns a failing exit code
  for significant measured regressions.
- CI runs 25 iterations and uploads the current and comparison JSON reports as
  build artifacts.

## Verification

- `backend/tests/test_rc229_performance_gate.py`: 3 passed, including a
  significant-regression injection that produces a failed gate.
- Targeted Ruff: passed.
- Strict Mypy for `benchmarks/performance_gate.py`: passed.
- Baseline self-comparison with `--check`: passed.
- A real 25-iteration RC-271 report was generated with Commit
  `6aa609f2d347331e79c38910bf2cf73b432c734e`; all nine measurements pass their
  absolute budgets. CLI `analyze` p95 is 917.953 ms, GUI cold-start p95 is
  1,794.780 ms, frontend dist is 829,010 bytes, and current-process RSS is
  64,110,592 bytes.
- The earlier JSON was captured from the same Git `HEAD` before the uncommitted
  RC-230 through RC-271 implementation existed, so the Commit alone did not
  identify equivalent source. `docs/performance/baseline.md` records the old
  and new measurements and the explicit RC-271 baseline migration. Thresholds
  were not relaxed; self-comparison passes with no regressions.

## Residual limits

The GUI probe measures the built frontend through a local HTTP harness and does
not claim native Tauri startup. Native release packaging and the cross-platform
desktop matrix remain separate platform verification work, not fabricated
values in this web GUI baseline. CI trend artifacts are available only in the CI
run that produces them.
