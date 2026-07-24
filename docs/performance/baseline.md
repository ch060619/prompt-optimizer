# Performance Baseline

## Contract

This is the `rc222-v1` baseline. Measurements use two warm-up calls followed
by 25 iterations, p50 is the median, and p95 is the nearest-rank 95th
percentile. The benchmark is offline and does not call a Provider or download
a model. The reproducible command is:

```powershell
.venv\Scripts\python.exe scripts/performance_baseline.py --iterations 25 --output docs/performance/baseline.json --check
```

The recorded JSON is `docs/performance/baseline.json`. The release gate is
also available with `--check`; it fails while any budget is exceeded or any
required probe is blocked.

## Fixed Environment

Recorded on 2026-07-19, Asia/Shanghai. The RC-271 baseline was regenerated
after the navigation, Agent, provider, audit, and frontend build changes were
present in the worktree. The JSON report is the source of truth.

| Field | Value |
| --- | --- |
| Machine | LENOVO 83DG |
| CPU | Intel Core i7-14650HX |
| RAM | 15.78 GiB |
| OS | Windows 11 Home Chinese, 10.0.26200 |
| Python | 3.12.10 |
| Node | v24.15.0 |
| Worktree | `6aa609f` |

## Measured Baseline

| Metric | p50 | p95 | Budget | Status |
| --- | ---: | ---: | ---: | --- |
| CLI `analyze` first response | 562.487 ms | 917.953 ms | <= 1000 ms | PASS |
| Offline rule first Token | 0.159 ms | 0.192 ms | <= 1500 ms | PASS |
| Indexed search query | 0.027 ms | 0.032 ms | <= 50 ms | PASS |
| Prompt diff | 0.015 ms | 0.020 ms | <= 50 ms | PASS |
| Frontend dist | 829,010 bytes | n/a | <= 2,000,000 bytes | PASS |
| GUI cold startup (frontend dist HTTP harness) | 1,225.139 ms | 1,794.780 ms | <= 3000 ms | PASS |
| GUI hot startup (frontend dist HTTP harness) | 13.522 ms | 23.926 ms | <= 500 ms | PASS |
| Current-process RSS | 64,110,592 bytes | n/a | <= 512,000,000 bytes | PASS |
| Backend wheel | 290,458 bytes | n/a | <= 5,000,000 bytes | PASS |

The CLI measurement launches the real
`python -m prompt_optimizer.cli.__main__ analyze` process, including Python
and local service startup. The offline first-Token measurement uses
`OfflineRuleProvider.stream()`; search uses 100 small Python files already
indexed by `SafeSearchIndexer`; diff uses two fixed PromptVersion objects.

## Probe Scope

The GUI rows use the built frontend served by a local HTTP harness. They cover
the repository's current GUI artifact without claiming a native desktop-shell
measurement; native Tauri packaging remains a separate platform build. RSS
uses the current benchmark process through Windows `GetProcessMemoryInfo` (or
`resource.getrusage` on POSIX), and backend size is the temporary wheel
produced by the local build backend. No external Provider request or model
download is involved.

## RC-229 Trend Gate

CI writes a fresh `rc222-v1` report with the current Commit, machine, CPU/OS
and runtime metadata, then compares measured metrics with
`benchmarks/performance_gate.py`. The gate tolerates a configured noise budget,
retains min/p50/p95/max statistics for both runs, skips probes that are blocked
in either run, and exits non-zero for a measured regression. The baseline now
satisfies all measured RC-222 budgets; the gate remains separate from native
packaging and cross-platform platform matrices.

## RC-271 Baseline Migration

The original report was captured before the RC-230 through RC-271 worktree
changes, although both reports had the same Git `HEAD` value. That value does
not identify uncommitted source changes, so comparing them as an unchanged
binary would produce a misleading regression. The new committed JSON baseline
was generated with the same 25-iteration command after the changes and keeps
the same budgets. The explicit deltas are:

- frontend dist decreased from 916,908 to 829,010 bytes after removing three
  unreferenced public image copies;
- backend RSS increased from 28,962,816 to 64,110,592 bytes because the
  expanded Agent/provider/audit module graph is loaded by the benchmark;
- CLI and GUI cold-start p95 are 917.953 ms and 1,794.780 ms respectively,
  both below their absolute budgets, with Windows process-launch variance
  retained in the raw report;
- backend wheel size changed from 288,943 to 290,458 bytes.

This is an intentional, documented RC-271 baseline migration, not a silent
threshold relaxation. A future change must compare against this JSON and still
pass the absolute budgets and trend gate.
