# RC-269 Evidence

<!-- RC ID: RC-269 -->

## Scope

Added local-only examples under `examples/` for a Provider-shaped adapter, bounded read-only tool, stdio MCP server/config, hashed plugin manifest/artifact, and workspace theme tokens. Added `docs/extensions/README.md` with stable/experimental API rules, SemVer/deprecation window, generated-contract checks, and minimum permissions.

## Verification

- `python -m pytest examples/test_examples.py -q`: 4 passed.
- `python scripts/check_docs.py --run`: passed and executes the marked example test.
- Tests cover deterministic Provider streaming, bounded tool output, MCP initialize/tool response, plugin hash/permission/enable/execute flow, and theme/config shape.

## Limits

Examples use no network, credentials, shell execution, or external service. They demonstrate extension boundaries and are not a claim that arbitrary third-party bundles are trusted.
