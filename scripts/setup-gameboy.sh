#!/usr/bin/env bash

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Game Boy desktop tools are only installed by this script on macOS."
    exit 0
fi

if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew is required to install the Game Boy development tools." >&2
    exit 1
fi

if ! brew list --versions rgbds >/dev/null 2>&1; then
    brew install rgbds
fi

for emulator in sameboy mgba-app; do
    if ! brew list --cask --versions "$emulator" >/dev/null 2>&1; then
        brew install --cask "$emulator"
    fi
done

echo "RGBDS $(rgbasm --version | awk '{print $2}')"
echo "SameBoy: /Applications/SameBoy.app"
echo "mGBA: /Applications/mGBA.app"
