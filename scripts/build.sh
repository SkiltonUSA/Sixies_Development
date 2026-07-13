#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/build" "$ROOT_DIR/src/generated"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to generate scroller tables." >&2
  exit 1
fi

if ! command -v acme >/dev/null 2>&1; then
  echo "ACME assembler is required. Install it with: brew install acme" >&2
  exit 1
fi

cd "$ROOT_DIR"
python3 scripts/generate_tables.py > src/generated/starwars_tables.inc
acme src/main.a
acme src/starwars_loader.a
acme src/starwars_direct.a
echo "Built build/bangalore.prg ($(stat -f%z build/bangalore.prg) bytes)"
echo "Built build/bangalore-direct.prg ($(stat -f%z build/bangalore-direct.prg) bytes)"
echo "Built build/bangalore-lite.prg ($(stat -f%z build/bangalore-lite.prg) bytes)"

cp src/assets/starwars/swcode.prg build/SWCODE.PRG
cp src/assets/starwars/basecode.prg build/SWBASE.PRG
cp src/assets/starwars/music.prg build/SWMUSIC.PRG
cp src/assets/starwars/disk.prg build/SWDISK.PRG
{
  printf '\000\310'
  cat src/assets/starwars/screen.bin
} > build/SWSCREEN.PRG
{
  printf '\000\375'
  cat src/assets/starwars/font.bin
} > build/SWFONT.PRG
{
  printf '\000\340'
  cat src/assets/starwars/text.bin
} > build/SWTEXT.PRG
{
  printf '\000\314'
  cat src/assets/starwars/sprites.bin
} > build/SWSPRITES.PRG

for companion in SWCODE SWSCREEN SWFONT SWTEXT SWSPRITES SWBASE SWMUSIC SWDISK; do
  cp "build/${companion}.PRG" "build/${companion}"
  cp "build/${companion}.PRG" "build/$(printf '%s' "$companion" | tr '[:upper:]' '[:lower:]')"
done

C1541_BIN="$(command -v c1541 || true)"
if [[ -z "$C1541_BIN" && -x /Applications/vice-arm64-sdl2-3.9/bin/c1541 ]]; then
  C1541_BIN=/Applications/vice-arm64-sdl2-3.9/bin/c1541
fi
if [[ -z "$C1541_BIN" && -x /Applications/vice-arm64-sdl2-3.9/VICE.app/Contents/Resources/bin/c1541 ]]; then
  C1541_BIN=/Applications/vice-arm64-sdl2-3.9/VICE.app/Contents/Resources/bin/c1541
fi

if [[ -n "$C1541_BIN" ]]; then
  rm -f build/bangalore.d64
  "$C1541_BIN" -format "bangalore,01" d64 build/bangalore.d64 \
    -write build/bangalore.prg BANGALORE \
    -write build/SWCODE.PRG SWCODE.PRG \
    -write build/SWSCREEN.PRG SWSCREEN.PRG \
    -write build/SWFONT.PRG SWFONT.PRG \
    -write build/SWTEXT.PRG SWTEXT.PRG \
    -write build/SWSPRITES.PRG SWSPRITES.PRG \
    -write build/SWBASE.PRG SWBASE.PRG \
    -write build/SWMUSIC.PRG SWMUSIC.PRG \
    -write build/SWDISK.PRG SWDISK.PRG >/dev/null
  echo "Built build/bangalore.d64"
else
  echo "c1541 not found; skipping D64 build"
fi

if command -v exomizer >/dev/null 2>&1; then
  exomizer sfx sys build/bangalore-lite.prg -o build/bangalore-lite_sfx.prg >/dev/null
  echo "Crunched build/bangalore-lite_sfx.prg ($(stat -f%z build/bangalore-lite_sfx.prg) bytes)"
else
  echo "exomizer not found; skipping crunched build (brew install exomizer)"
fi
