#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="$ROOT_DIR/.tools/acme/bin"
DEST_BIN="$DEST_DIR/acme"

if [[ -x "$DEST_BIN" ]]; then
  echo "ACME already available at $DEST_BIN"
  "$DEST_BIN" --version
  exit 0
fi

if ! command -v acme >/dev/null 2>&1; then
  echo "ACME was not found on PATH." >&2
  echo "Install it first, for example on macOS: brew install acme" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
cp "$(command -v acme)" "$DEST_BIN"
chmod +x "$DEST_BIN"

echo "Workspace-local ACME ready at $DEST_BIN"
"$DEST_BIN" --version
