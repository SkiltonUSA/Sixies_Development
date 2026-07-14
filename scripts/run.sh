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

exec "$VICE_BIN" -autostart "$BUILD_DIR/StarwarsScrollerDemo.prg"
