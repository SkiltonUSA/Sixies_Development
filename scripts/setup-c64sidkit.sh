#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOL_DIR="$ROOT_DIR/.tools/c64SIDkit"
VENV_DIR="$TOOL_DIR/.venv"
REPOSITORY="https://github.com/devinvenable/c64SIDkit.git"

if [[ ! -d "$TOOL_DIR/.git" ]]; then
  git clone --depth 1 "$REPOSITORY" "$TOOL_DIR"
fi

if [[ ! -x "$VENV_DIR/bin/sid-sfx" ]]; then
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install -e "$TOOL_DIR[tools]"
fi

echo "Workspace-local c64SIDkit ready at $TOOL_DIR"
"$VENV_DIR/bin/sid-sfx" play --list
