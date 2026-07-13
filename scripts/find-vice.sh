#!/usr/bin/env bash

set -euo pipefail

for candidate in \
  "$(command -v x64sc || true)" \
  "$(command -v x64 || true)" \
  /Applications/vice-arm64-sdl2-3.9/bin/x64sc \
  /Applications/vice-x86-64-sdl2-3.9/bin/x64sc \
  /Applications/VICE/x64sc.app/Contents/MacOS/x64sc
do
  if [[ -n "$candidate" && -x "$candidate" ]]; then
    printf '%s\n' "$candidate"
    exit 0
  fi
done

echo "VICE x64sc was not found. Install VICE or open build/bangalore.prg in your emulator." >&2
exit 1
