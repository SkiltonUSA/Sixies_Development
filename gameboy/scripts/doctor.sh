#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GAMEBOY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$GAMEBOY_DIR/.." && pwd)"
GBDK_DIR="$ROOT_DIR/.tools/gameboy/gbdk"
CORE_ONLY=0

if [[ "${1:-}" == "--core" ]]; then
    CORE_ONLY=1
elif [[ $# -ne 0 ]]; then
    echo "Usage: $0 [--core]" >&2
    exit 2
fi

missing=()
for tool_path in \
    "$GBDK_DIR/bin/lcc" \
    "$GBDK_DIR/bin/png2asset" \
    "$GBDK_DIR/bin/romusage"; do
    [[ -x "$tool_path" ]] || missing+=("$tool_path")
done

for command_name in make python3; do
    command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
done

if [[ "$CORE_ONLY" -eq 0 && "$(uname -s)" == "Darwin" ]]; then
    for command_name in rgbasm rgbfix rgbgfx rgblink; do
        command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
    done

    for app_path in \
        "/Applications/SameBoy.app" \
        "/Applications/mGBA.app" \
        "/Applications/Tiled.app" \
        "$ROOT_DIR/.tools/gameboy/hUGETracker/hUGETracker.app"; do
        [[ -e "$app_path" ]] || missing+=("$app_path")
    done
fi

if [[ ${#missing[@]} -ne 0 ]]; then
    echo "Missing Game Boy tools:" >&2
    printf '  %s\n' "${missing[@]}" >&2
    echo "Run: make -C gameboy setup" >&2
    exit 1
fi

echo "Game Boy development environment is ready."
echo "  GBDK:    $($GBDK_DIR/bin/lcc -v 2>&1 | head -n 1)"
echo "  assets:  $GBDK_DIR/bin/png2asset"
echo "  usage:   $GBDK_DIR/bin/romusage"

if [[ "$CORE_ONLY" -eq 0 && "$(uname -s)" == "Darwin" ]]; then
    echo "  RGBDS:   $(rgbasm --version | head -n 1)"
    echo "  primary: /Applications/SameBoy.app"
    echo "  second:  /Applications/mGBA.app"
    echo "  maps:    /Applications/Tiled.app"
    echo "  music:   $ROOT_DIR/.tools/gameboy/hUGETracker/hUGETracker.app"
fi
