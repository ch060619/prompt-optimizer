# RC-223 Evidence

## Scope

Extended `SafeSearchIndexer` with `start_background_scan()`. A bounded
`Queue(maxsize=...)` connects a path producer to the existing filter/cache
consumer, so the caller receives a handle immediately and the scan cannot
accumulate an unbounded path list. The existing synchronous `scan()` remains
available and now shares the same path processor.

Ignore files, sensitive paths, symlinks, binary files, file-size limits, and
mtime/size/hash cache behavior remain in one search boundary. `BackgroundScan`
exposes status, entries, `wait(timeout)`, and cancellation; cancellation
before work starts is explicit and does not wait on the queue.

## Verification

- `python -m pytest backend/tests/test_rc083_search_index.py backend/tests/test_rc223_search_index.py -q`: 4 passed, 1 skipped.
- `python -m ruff check` for the search index and RC-083/RC-223 tests: passed.
- `python -m mypy --follow-imports skip backend/rabbit_code/search_index.py`: passed.
- `python -m compileall -q` for the search index and RC-223 tests: passed.

## Residual limits

No real million-file repository, cross-process worker, or Linux filesystem
pressure test was available. The bounded queue and cancellation contract are
process-local; a future distributed index service is not required by this
boundary and was not added.
