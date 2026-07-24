# RC-239 Evidence

## Scope

Added `backend/tests/test_rc239_security_matrix.py` for command-injection
classification, workspace path escape, dangerous environment variables, artifact destination
escape, and unapproved trust permissions. Existing RC-206/207/208/209/211/221 tests cover
secret leaks, sensitive files, loopback boundaries, plugin/MCP trust and hash rechecks,
artifact verification, security docs/SBOM, and portable archive traversal.

## Verification

```text
python -m pytest backend/tests/test_rc239_security_matrix.py -q
python -m pytest backend/tests/test_rc239_security_matrix.py backend/tests/test_rc211_security_engineering.py backend/tests/test_rc207_local_api_security.py backend/tests/test_rc208_trust.py backend/tests/test_rc209_artifacts.py backend/tests/test_rc221_portable.py -q
python scripts/security_scan.py --check
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; .venv\Scripts\pip-audit.exe
```

Results: RC-239 `5 passed`; combined security regression `25 passed`; repository security
gate passed; pip-audit reported `No known vulnerabilities found`.

## Limits

No real malicious repository, remote MCP/plugin, external supply-chain traffic, or real
Provider penetration test was run. The local package `rabbit-code` and
`rabbit-code-protocol` are intentionally not published to PyPI and were skipped by
pip-audit with an explicit reason.
