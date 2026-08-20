#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: package_disk.sh INPUT_BINARY OUTPUT_DSK ASSET_DIR" >&2
  exit 1
fi

INPUT_BINARY="$1"
OUTPUT_DSK="$2"
ASSET_DIR="$3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLE2_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$APPLE2_DIR/.." && pwd)"
TOOLS_DIR="$ROOT_DIR/.tools"
APPLECOMMANDER_JAR="$(ls "$TOOLS_DIR"/applecommander/AppleCommander-ac-*.jar | head -n 1)"
PRODOS_TEMPLATE="$TOOLS_DIR/apple2-prodos/ProDOS_2_4_3.po"
JAVA_BIN="${JAVA_BIN:-/opt/homebrew/opt/openjdk/bin/java}"
TARGET_PATH="$(cl65 --print-target-path)"
LOADER_SYSTEM="$TARGET_PATH/apple2/util/loader.system"

if [[ ! -f "$APPLECOMMANDER_JAR" ]]; then
  echo "AppleCommander jar not found." >&2
  exit 1
fi

if [[ ! -f "$PRODOS_TEMPLATE" ]]; then
  echo "Bootable ProDOS template not found." >&2
  exit 1
fi

if [[ ! -x "$JAVA_BIN" ]]; then
  JAVA_BIN="$(command -v java || true)"
fi

if [[ -z "$JAVA_BIN" || ! -x "$JAVA_BIN" ]]; then
  echo "A working Java runtime was not found." >&2
  exit 1
fi

template_files=(
  VIEW.README
  BITSY.BOOT
  QUIT.SYSTEM
  BASIC.SYSTEM
  COPYIIPLUS.8.4
  BLOCKWARDEN
  CAT.DOCTOR
  UNSHRINK
  CD.EXT
  FASTDSK
  FASTDSK.CONF
  FASTDSK.SYSTEM
  MAKE.SMALL.P8
  MINIBAS
  MR.FIXIT.Y2K
  README
)

cp "$PRODOS_TEMPLATE" "$OUTPUT_DSK"
for filename in "${template_files[@]}"; do
  "$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" -d "$OUTPUT_DSK" "$filename"
done
"$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" -n "$OUTPUT_DSK" SIXIES
"$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" -p "$OUTPUT_DSK" SIXIES.SYSTEM sys < "$LOADER_SYSTEM"
"$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" -as "$OUTPUT_DSK" SIXIES < "$INPUT_BINARY"

for filename in TITLE.MAIN TITLE.AUX GAMEOVER.MAIN GAMEOVER.AUX GRID.A2FM DICE.BLITS MERGESTAR \
  FX00 FX01 FX02 FX03 FX04 FX05 FX06 FX07 FX08 FX09; do
  if [[ ! -f "$ASSET_DIR/$filename" ]]; then
    echo "DHGR asset not found: $ASSET_DIR/$filename" >&2
    exit 1
  fi
  "$JAVA_BIN" -jar "$APPLECOMMANDER_JAR" -p "$OUTPUT_DSK" "$filename" bin < "$ASSET_DIR/$filename"
done
