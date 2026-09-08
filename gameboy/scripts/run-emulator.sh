#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <sameboy|mgba> <rom>" >&2
    exit 2
fi

emulator="$1"
rom_path="$2"

if [[ ! -f "$rom_path" ]]; then
    echo "ROM not found: $rom_path" >&2
    exit 1
fi

case "$emulator" in
    sameboy)
        if [[ "$(uname -s)" == "Darwin" && -d /Applications/SameBoy.app ]]; then
            open -a SameBoy "$rom_path"
        elif command -v sameboy >/dev/null 2>&1; then
            sameboy "$rom_path"
        else
            echo "SameBoy is not installed. Run: make -C gameboy setup" >&2
            exit 1
        fi
        ;;
    mgba)
        if [[ "$(uname -s)" == "Darwin" && -d /Applications/mGBA.app ]]; then
            open -a mGBA "$rom_path"
        elif command -v mgba >/dev/null 2>&1; then
            mgba "$rom_path"
        else
            echo "mGBA is not installed. Run: make -C gameboy setup" >&2
            exit 1
        fi
        ;;
    *)
        echo "Unknown emulator: $emulator" >&2
        exit 2
        ;;
esac
