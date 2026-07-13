#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$ROOT_DIR/scripts/build.sh"
VICE_BIN="$("$ROOT_DIR/scripts/find-vice.sh")"
BUILD_DIR="$ROOT_DIR/build"

if [[ "${RUN_D64:-0}" == "1" && -f "$BUILD_DIR/bangalore.d64" ]]; then
  exec "$VICE_BIN" \
    +drive8truedrive \
    -8 "$BUILD_DIR/bangalore.d64" \
    -autostart "$BUILD_DIR/bangalore.d64"
fi

MON_FILE="$ROOT_DIR/.context/run-preload.mon"
mkdir -p "$ROOT_DIR/.context"
cat >"$MON_FILE" <<EOF
load "$BUILD_DIR/SWCODE.PRG" 0
load "$BUILD_DIR/SWSCREEN.PRG" 0
load "$BUILD_DIR/SWFONT.PRG" 0
load "$BUILD_DIR/SWTEXT.PRG" 0
load "$BUILD_DIR/SWSPRITES.PRG" 0
load "$BUILD_DIR/SWBASE.PRG" 0
load "$BUILD_DIR/SWMUSIC.PRG" 0
load "$BUILD_DIR/SWDISK.PRG" 0
load "$BUILD_DIR/bangalore-direct.prg" 0
g c000
EOF

exec "$VICE_BIN" \
  -moncommands "$MON_FILE" \
  -initbreak ready
