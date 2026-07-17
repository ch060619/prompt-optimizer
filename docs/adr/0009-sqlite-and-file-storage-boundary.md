# ADR-0009：SQLite 与版本化文件存储边界

- RC ID: RC-064
- Status: Accepted for the current local storage boundary
- Date: 2026-07-17
- Deciders: Rabbit Code engineering

## Decision

SQLite is the source of truth for structured metadata: users, projects, prompt versions, tasks,
future sessions, and indexes. Large or replaceable payloads use a sibling versioned file layout:

```text
<app-data>/
  rabbit-code.sqlite3
  files/
    v1/
      logs/
      attachments/
      models/
      cache/
```

`FileStore` owns the file categories and rejects absolute, traversal, unsupported-category, and
empty keys. The database schema version and file layout version are independent so either boundary
can migrate without treating a model or attachment as a SQLite row.

## Write and Concurrency Rules

- Each SQLite write uses the existing connection context as one transaction. Connections enable
  foreign keys, a 30-second busy timeout, and WAL mode for concurrent local readers/writers.
- Schema migration remains backup-first. A migration failure leaves the source database unchanged;
  the existing RC-053 backup/restore contract remains the recovery boundary.
- Each file write creates a sibling temporary file, writes and flushes the complete payload, calls
  `fsync`, and replaces the destination with `os.replace`. Temporary files are removed on success or
  injected failure. The process-local lock serializes FileStore operations in one process; atomic
  replacement also prevents readers from observing half-written content.
- Cache cleanup may remove only `files/v1/cache`. It cannot remove SQLite metadata, logs,
  attachments, or models.

## Consequences and Limits

The boundary now has deterministic concurrent-write and crash-injection coverage. Session metadata
and indexes remain SQLite responsibilities even though the current product has not implemented all
session tables. Cross-process file locking, encrypted model/attachment storage, quotas, retention,
and distributed storage are outside this local RC and require separate security or lifecycle work.
