# RC-158 Evidence

<!-- RC ID: RC-158. -->

## Delivered

- `data/evaluation/prompts.yml` is versioned as `rc-158-v1` with fixed random
  seed `158` and 60 cases.
- The dataset covers coding, business, education, creative, long text, code
  blocks, variables, Chinese, and adversarial input, with the existing support,
  data, and technical regression cases preserved.
- The evaluation report defines analyzer automatic scoring and a two-reviewer
  blind-review protocol, and emits deterministic blind-review batch IDs.

## Validation

- `backend/tests/test_rc158_evaluation.py` and the existing evaluation test:
  3 passed.
- Ruff and Mypy for the RC-158 evaluation service and test: PASS.
- Baseline report: `docs/evaluation-report.md`.

## Known Environment Limits

- The bundled Python runtime did not include pytest, Ruff, Mypy, or PyYAML.
  Direct `.venv/Scripts/python.exe` invocation was available for validation.
- The installed CLI entry point could not import the repository's `rabbit_code`
  source package, so the baseline report was generated through the same service
  with `backend/src` and `backend` on the source path.
- Full Vite build remains blocked by the existing sandbox directory permission
  issue.
