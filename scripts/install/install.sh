#!/bin/sh
# Rabbit Code CLI installer for Linux.
# Usage: curl -fsSL https://rabbit-code.dev/install.sh | sh
set -e

echo "Rabbit Code CLI Installer for Linux"

# Check Python
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Error: $PYTHON not found. Install Python 3.12+ first." >&2
  exit 1
fi

PY_VERSION=$("$PYTHON" --version 2>&1)
echo "Using: $PY_VERSION"

# Install package
PKG="rabbit-code"
VERSION="${VERSION:-}"
if [ -n "$VERSION" ]; then
  PKG="$PKG==$VERSION"
fi
echo "Installing $PKG from PyPI..."
"$PYTHON" -m pip install --user --upgrade "$PKG"

# Verify
if command -v rabbit >/dev/null 2>&1; then
  RABBIT_VERSION=$(rabbit version 2>&1)
  echo "Installed: $RABBIT_VERSION"
  echo "Run 'rabbit --help' to get started."
else
  echo "Warning: rabbit command not found in PATH."
  echo "Try: python3 -m prompt_optimizer.cli.app version"
  echo "You may need to add ~/.local/bin to your PATH."
fi
