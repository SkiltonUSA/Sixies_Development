#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/build"

if ! command -v acme >/dev/null 2>&1; then
  echo "ACME assembler is required. Install it with: brew install acme" >&2
  exit 1
fi

cd "$ROOT_DIR"
python3 scripts/generate_transition_backdrop.py
acme src/transition_browser.a

echo "Built build/transition_browser.prg"

if command -v exomizer >/dev/null 2>&1; then
  exomizer sfx sys build/transition_browser.prg -o build/transition_browser_sfx.prg >/dev/null
  echo "Crunched build/transition_browser_sfx.prg ($(stat -f%z build/transition_browser_sfx.prg) bytes)"
else
  echo "exomizer not found; skipping crunched build (brew install exomizer)"
fi
