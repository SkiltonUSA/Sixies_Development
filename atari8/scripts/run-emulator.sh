#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: run-emulator.sh <xex-or-atr> [64|128]" >&2
    exit 2
fi

IMAGE="$1"
MEMORY="${2:-64}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROM="$ROOT_DIR/.tools/atari8/roms/ATARIXL.ROM"

if [[ ! -f "$ROM" ]]; then
    echo "Atari XL/XE ROM is missing; run make -C atari8 setup-tools." >&2
    exit 1
fi

machine=(-xl)
if [[ "$MEMORY" == "128" ]]; then
    machine=(-xe)
fi

image_args=("$IMAGE")
if [[ "$IMAGE" == *.xex || "$IMAGE" == *.XEX ]]; then
    image_args=(-run "$IMAGE")
fi

exec atari800 \
    -no-autosave-config \
    "${machine[@]}" \
    -ntsc -nobasic -xlxe_rom "$ROM" \
    -ntsc-filter-preset monochrome \
    -no-kbdjoy0 -kbdjoy1 -windowed \
    "${image_args[@]}"
