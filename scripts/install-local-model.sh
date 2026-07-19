#!/usr/bin/env sh
set -eu

# RC IDs: RC-185, RC-199. Keep POSIX Shell user-scoped and never invoke elevation.
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
elif [ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]; then
  PYTHON="$ROOT_DIR/.venv/Scripts/python.exe"
else
  PYTHON=$(command -v python3 || command -v python)
fi

export PYTHONPATH="$ROOT_DIR/backend/src:$ROOT_DIR/backend:$ROOT_DIR/packages/protocol${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON" "$ROOT_DIR/scripts/local_model_install.py" "$@"
