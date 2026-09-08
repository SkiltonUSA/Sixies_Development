#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
TRACKER_APP="$ROOT_DIR/.tools/gameboy/hUGETracker/hUGETracker.app"

if [[ ! -d "$TRACKER_APP" ]]; then
    echo "hUGETracker is not installed. Run: make -C gameboy setup" >&2
    exit 1
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "The bundled hUGETracker launcher is for macOS." >&2
    exit 1
fi

open "$TRACKER_APP"
