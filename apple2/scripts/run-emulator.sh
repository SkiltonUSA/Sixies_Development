#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: run-emulator.sh DISK_IMAGE [trace]" >&2
  exit 1
fi

DISK_IMAGE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
TRACE_MODE="${2:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
IZAPPLE2_BIN="$ROOT_DIR/.tools/izapple2/izapple2"
RUN_DIR="$ROOT_DIR/apple2/build/emulator"
RUN_DISK="$RUN_DIR/sixies-run.po"

if [[ ! -f "$DISK_IMAGE" ]]; then
  echo "Disk image not found: $DISK_IMAGE" >&2
  exit 1
fi

if [[ ! -x "$IZAPPLE2_BIN" ]]; then
  echo "izapple2 is not installed. Run: make -C apple2 setup-tools" >&2
  exit 1
fi

mkdir -p "$RUN_DIR"
cp "$DISK_IMAGE" "$RUN_DISK"

args=(
  -model=2enh
  -rgb
  -s2=empty
  -s3=empty
  -s4=empty
)

if [[ "$TRACE_MODE" == "trace" ]]; then
  args+=("-trace=mli")
fi

exec "$IZAPPLE2_BIN" "${args[@]}" "$RUN_DISK"
