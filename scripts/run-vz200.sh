#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET="${1:?usage: run-vz200.sh build/vz200/SIXIES.VZ}"
ROM_DIR="$ROOT_DIR/.tools/mame/roms"
LOG_FILE="$ROOT_DIR/.context/mame-vz200.log"
PID_FILE="$ROOT_DIR/.context/mame-vz200.pid"
JOB_LABEL="com.sixies.vz200"
JOB_DOMAIN="gui/$(id -u)"

if ! command -v mame >/dev/null 2>&1; then
  echo "MAME is missing. Run: make setup-vz200-dev" >&2
  exit 1
fi

if [[ ! -f "$TARGET" ]]; then
  echo "VZ snapshot is missing: $TARGET" >&2
  exit 1
fi

if [[ ! -d "$ROM_DIR/vz200" ]]; then
  echo "VZ200 MAME ROMs are missing from $ROM_DIR/vz200." >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/.context"
TARGET="$(cd "$(dirname "$TARGET")" && pwd)/$(basename "$TARGET")"
MAME_BIN="$(command -v mame)"

launchctl remove "$JOB_LABEL" 2>/dev/null || true
launchctl submit -l "$JOB_LABEL" -o "$LOG_FILE" -e "$LOG_FILE" -- \
  "$MAME_BIN" vz200 -rompath "$ROM_DIR" -snapshot "$TARGET" -window -skip_gameinfo
launchctl kickstart -k "$JOB_DOMAIN/$JOB_LABEL"

sleep 1
MAME_PID="$(launchctl print "$JOB_DOMAIN/$JOB_LABEL" | awk '/^[[:space:]]*pid =/ { print $3; exit }')"
if ! kill -0 "$MAME_PID" 2>/dev/null; then
  cat "$LOG_FILE" >&2 || true
  echo "MAME exited during startup." >&2
  exit 1
fi

echo "$MAME_PID" > "$PID_FILE"
echo "MAME VZ200 started (PID $MAME_PID)."
