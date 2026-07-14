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
python3 scripts/generate_tables.py
python3 scripts/generate_sid_frequency_table.py
python3 scripts/generate_midi_markov_sid.py
python3 scripts/generate_galway_sid.py
python3 scripts/generate_logo.py
acme src/main.a
acme -DSPARKLE_PAYLOAD=1 src/main.a
acme src/starwars_loader.a
acme src/starwars_direct.a
acme src/music/starwars_40s.a
acme src/music/galway_nights.a
python3 scripts/package_sid.py
echo "Built build/StarwarsScrollerDemo.prg ($(stat -f%z build/StarwarsScrollerDemo.prg) bytes)"
echo "Built build/StarwarsScrollerDemo-sparkle-part.prg ($(stat -f%z build/StarwarsScrollerDemo-sparkle-part.prg) bytes)"
echo "Built build/StarwarsScrollerDemo-loader.prg ($(stat -f%z build/StarwarsScrollerDemo-loader.prg) bytes)"
echo "Built build/StarwarsScrollerDemo-direct.prg ($(stat -f%z build/StarwarsScrollerDemo-direct.prg) bytes)"

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
  rm -f build/StarwarsScrollerDemo.d64
  "$C1541_BIN" -format "starwars demo,01" d64 build/StarwarsScrollerDemo.d64 \
    -write build/StarwarsScrollerDemo-loader.prg STARWARSSCROLLERDEMO \
    -write build/SWCODE.PRG SWCODE.PRG \
    -write build/SWSCREEN.PRG SWSCREEN.PRG \
    -write build/SWFONT.PRG SWFONT.PRG \
    -write build/SWTEXT.PRG SWTEXT.PRG \
    -write build/SWSPRITES.PRG SWSPRITES.PRG \
    -write build/SWBASE.PRG SWBASE.PRG \
    -write build/SWMUSIC.PRG SWMUSIC.PRG \
    -write build/SWDISK.PRG SWDISK.PRG >/dev/null
  echo "Built build/StarwarsScrollerDemo.d64"
else
  echo "c1541 not found; skipping D64 build"
fi

python3 scripts/generate_sparkle_sls.py
