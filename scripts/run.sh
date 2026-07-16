#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/build.sh"
VICE_BIN="$("$ROOT_DIR/scripts/find-vice.sh")"
BUILD_DIR="$ROOT_DIR/build"

if [[ "${RUN_D64:-0}" == "1" && -f "$BUILD_DIR/StarwarsScrollerDemo.d64" ]]; then
  exec "$VICE_BIN" \
    +drive8truedrive \
    -8 "$BUILD_DIR/StarwarsScrollerDemo.d64" \
    -autostart "$BUILD_DIR/StarwarsScrollerDemo.d64"
fi

RUN_PRG="$BUILD_DIR/StarwarsScrollerDemo-sfx.prg"
if [[ ! -f "$RUN_PRG" ]]; then
  RUN_PRG="$BUILD_DIR/StarwarsScrollerDemo.prg"
fi

# The native image contains data beneath C64 I/O and ROM. Inject mode avoids
# VICE preferences that otherwise mount a PRG as a temporary, slow disk image;
# the SFX build then decrunches the complete memory layout itself.
exec "$VICE_BIN" \
  -autostartprgmode 1 \
  -autostart "$RUN_PRG"
