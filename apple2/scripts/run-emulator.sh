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
APPLECOMMANDER_JAR="$(find "$ROOT_DIR/.tools/applecommander" -name 'AppleCommander-ac-*.jar' -print -quit 2>/dev/null || true)"
JAVA_BIN="${JAVA_BIN:-/opt/homebrew/opt/openjdk/bin/java}"

if [[ ! -f "$DISK_IMAGE" ]]; then
  echo "Disk image not found: $DISK_IMAGE" >&2
  exit 1
fi

if [[ ! -x "$IZAPPLE2_BIN" ]]; then
  echo "izapple2 is not installed. Run: make -C apple2 setup-tools" >&2
  exit 1
fi

mkdir -p "$RUN_DIR"

# Refresh the release disk without discarding scores saved by the previous run.
high_score_backup=""
cleanup_high_score_backup() {
  if [[ -n "$high_score_backup" && -f "$high_score_backup" ]]; then
    unlink "$high_score_backup"
  fi
}
trap cleanup_high_score_backup EXIT

if [[ -f "$RUN_DISK" && -n "$APPLECOMMANDER_JAR" ]]; then
  if [[ ! -x "$JAVA_BIN" ]]; then
    JAVA_BIN="$(command -v java || true)"
  fi
  if [[ -n "$JAVA_BIN" && -x "$JAVA_BIN" ]]; then
    high_score_backup="$(mktemp "$RUN_DIR/hiscore.XXXXXX")"
    if ! "$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" \
        -g "$RUN_DISK" HISCORE "$high_score_backup" >/dev/null 2>&1; then
      unlink "$high_score_backup"
      high_score_backup=""
    fi
  fi
fi

cp "$DISK_IMAGE" "$RUN_DISK"

if [[ -n "$high_score_backup" ]]; then
  "$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" -d "$RUN_DISK" HISCORE >/dev/null
  "$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" \
    -p "$RUN_DISK" HISCORE bin < "$high_score_backup"
  unlink "$high_score_backup"
  high_score_backup=""
fi

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
