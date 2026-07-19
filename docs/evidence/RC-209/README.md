# RC-209 Evidence

## Scope

Added a shared versioned `ArtifactManifest` and `ArtifactDownloader` for
binary, model, update, and plugin artifacts. Manifests require an HTTPS source
URL, SHA-256 digest, license identifier, HTTPS license URL, license version,
and license summary. Downloads require explicit confirmation of the exact
license version. Bytes are written to a randomized `.part` file, verified, and
atomically promoted only after the digest matches; failures remove the
temporary file and never replace an existing destination.

`ModelSpec.to_artifact_manifest()` now reuses the same HTTPS, license, and
hash policy, so the controlled Gemma/Qwen model manifest cannot declare an
insecure source or license URL.

## Verification

- `python -m pytest backend/tests/test_rc209_artifacts.py backend/tests/test_rc188_model_manifest.py backend/tests/test_rc191_downloader.py backend/tests/test_rc192_distribution.py backend/tests/test_rc200_offline_import.py backend/tests/test_rc077_plugins.py -q`: 28 passed.
- `python -m ruff check` for artifact, model manifest, plugin, download, distribution, offline import, and RC-209 test files: passed.
- `python -m mypy --strict --explicit-package-bases` with `MYPYPATH=backend/src;backend;packages/protocol` for artifact, model manifest, and RC-209 tests: passed.
- `python -m compileall -q` for artifact, model manifest, and RC-209 tests: passed.

Tests cover all four artifact kinds, manifest serialization, successful atomic
installation, hash mismatch, unavailable HTTPS source, missing license
confirmation, temporary-file cleanup, old-version preservation, and model
manifest reuse.

## Residual limits

No real external HTTP request was made. The downloader accepts an injected
fetcher so CI remains offline and cost-free; production transport, proxy
behavior, and signed releases remain outside this item. Digital signatures
are intentionally not required by the execution plan.
