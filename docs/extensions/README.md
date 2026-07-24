# Extension Examples and API Versioning

The examples in this directory are intentionally small and local-only. They demonstrate boundaries, not a promise that every extension is enabled in the default UI.

## Examples

- `provider_adapter.py`: a deterministic Provider-shaped adapter with no network call.
- `tool.py`: a read-only workspace summary tool using a bounded file count.
- `mcp_server.py` and `mcp-server.json`: a stdio JSON-RPC example with one read-only tool.
- `plugin/`: a local plugin manifest and artifact hash contract.
- `theme/theme.json`: a minimal theme token extension.
- `test_examples.py`: tests for all examples without external services.

All examples use the minimum permission (`read`) and avoid credentials, network access, shell execution, and writes outside a caller-selected temporary directory.

<!-- docs-check:run -->
```python
python -m pytest examples/test_examples.py -q
```

## Stable and experimental APIs

- Stable APIs are the versioned Python contracts under `packages/protocol`, the `/api/v1` FastAPI routes, the CLI command names documented in `docs/user-guide.md`, and the manifest fields tested by this repository.
- Experimental APIs are marked in source/docstrings, may change within a minor release, and must not be used by the installer or stable UI without an adapter.
- Breaking changes require a major version according to SemVer. Additive fields are optional first; removing or changing meaning requires a deprecation window and migration note.
- API deprecations are announced for at least one minor release and remain readable for the documented compatibility window. Regeneration and compatibility tests must fail when a stable contract drifts.

The generated API files are checked by `scripts/generate_api.py --check`. Protocol changes also require a migration/compatibility test and an entry in the changelog.
