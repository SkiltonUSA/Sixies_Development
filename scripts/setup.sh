#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Workspace: $ROOT_DIR"

if command -v python3 >/dev/null 2>&1; then
  echo "python3: ok ($(command -v python3))"
else
  echo "python3: missing"
fi

if command -v acme >/dev/null 2>&1; then
  echo "acme: ok ($(command -v acme))"
else
  echo "acme: missing"
  echo "install hint: brew install acme"
fi

if vice_bin="$("$ROOT_DIR/scripts/find-vice.sh" 2>/dev/null)"; then
  echo "vice: ok ($vice_bin)"
else
  echo "vice: missing"
  echo "install hint: add x64sc or x64 to PATH, or install VICE.app in /Applications"
fi

echo "Next: run ./scripts/build.sh or use Conductor Run after dependencies are installed."
