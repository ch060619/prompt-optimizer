# RC-240 Evidence

## Scope

Added `scripts/check_rc240_quality.py`, its deterministic report at
`docs/evidence/RC-240/quality-report.json`, and
`backend/tests/test_rc240_quality_gate.py`. The gate runs the fixed `rc-158-v1` dataset
(seed 158, 60 cases), compares analyzer scores, records SequenceMatcher similarity and an
exact normalized prompt anchor, and requires protected structure signatures and language
profiles to remain valid. Results are grouped by Provider/model.

## Verification

```text
python scripts/check_rc240_quality.py --check
python -m pytest backend/tests/test_rc240_quality_gate.py -q
.venv\Scripts\ruff.exe check scripts/check_rc240_quality.py backend/tests/test_rc240_quality_gate.py
```

Results: `60/60` quality cases passed; `offline/rules` had 60 cases and average score delta
`72.8`; the focused test passed and Ruff passed.

## Limits

The report preserves the dataset's two-reviewer blind-review protocol, but no human blind
ratings or real cloud Provider calls were performed in this offline run. Those remain
controlled evaluation inputs rather than invented scores.
