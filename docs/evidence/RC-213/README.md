# RC-213 Evidence

## Scope

Added docs/data-model/schema-v1.json as the single source for ten core
entities: workspace, session, message, content block, tool call, file
snapshot, prompt version, provider reference, model manifest, and setting.
The schema defines IDs, scope, timestamps, soft-delete fields, version fields,
relationships, deletion behavior, and indexes. SecretStore credentials are
represented only by opaque references; file paths use an opaque/redacted
reference field.

scripts/generate_data_model.py deterministically renders the Mermaid ER
diagram, backend/migrations/0002_core_data_model.sql, Pydantic models, and
TypeScript interfaces. The generated artifacts are checked by the workspace
gate.

## Verification

- .venv\Scripts\python.exe -m pytest backend/tests/test_rc213_data_model.py -q: 2 passed.
- The generated migration executed successfully against a temporary SQLite database.
- Generated artifact drift check, Ruff, strict Mypy, workspace.py check, and
  frontend TypeScript/Vite build: passed.

## Residual limits

The SQL file is an initial migration draft. The existing RC-054
StorageService schema v1 remains active until RC-214 supplies migration
execution, transaction, concurrency, backup, restore, and integrity behavior.
