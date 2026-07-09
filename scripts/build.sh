#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/build"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to generate the filled sinewave tables." >&2
  exit 1
fi

if ! command -v acme >/dev/null 2>&1; then
  echo "ACME assembler is required. Install it with: brew install acme" >&2
  exit 1
fi

cd "$ROOT_DIR"
python3 scripts/generate_filled_sine.py
acme src/main.a

echo "Built build/cancun.prg"

if command -v exomizer >/dev/null 2>&1; then
  exomizer sfx sys build/cancun.prg -o build/cancun_sfx.prg >/dev/null
  echo "Crunched build/cancun_sfx.prg ($(stat -f%z build/cancun_sfx.prg) bytes)"
else
  echo "exomizer not found; skipping crunched build (brew install exomizer)"
fi
