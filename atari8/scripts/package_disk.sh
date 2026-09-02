#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "usage: package_disk.sh <dir2atr> <input.xex> <output.atr>" >&2
    exit 2
fi

DIR2ATR="$1"
INPUT_XEX="$2"
OUTPUT_ATR="$3"
DISK_DIR="$(dirname "$OUTPUT_ATR")/disk-root"

rm -rf "$DISK_DIR"
mkdir -p "$DISK_DIR"
cp "$INPUT_XEX" "$DISK_DIR/SIXIES.XEX"
"$DIR2ATR" -S -b PicoBoot406 "$OUTPUT_ATR" "$DISK_DIR"
