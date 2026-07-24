# Performance Benchmarks

The reproducible workload is defined by `scripts/performance_baseline.py`: it
uses a fixed offline prompt, 100 generated Python files, fixed PromptVersion
objects, and the offline rule Provider. It does not call a cloud Provider or
download a model.

Generate a CI report and compare it with the committed baseline:

```powershell
.venv\Scripts\python.exe scripts/performance_baseline.py --iterations 15 --output performance-current.json
.venv\Scripts\python.exe benchmarks/performance_gate.py --baseline docs/performance/baseline.json --current performance-current.json --comparison-output performance-comparison.json --check
```

The comparison keeps blocked probes as skipped, records baseline/current
environment metadata and min/p50/p95/max statistics, and exits non-zero only
for a measured regression beyond the configured noise budget.
