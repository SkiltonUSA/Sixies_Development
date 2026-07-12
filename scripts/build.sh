#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$ROOT_DIR/build"

if ! command -v acme >/dev/null 2>&1; then
  echo "ACME assembler is required. Install it with: brew install acme" >&2
  exit 1
fi

cd "$ROOT_DIR"
acme src/main.a
acme src/starwars_launcher.a
cp src/assets/starwars/swcode.prg build/SWCODE.PRG
cp /Users/dskilton/conductor/workspaces/c64u/cancun/.context/NoBoundsSource/NoBounds/Link/MAIN/Main-BaseCode.prg build/SWBASE.PRG
cp /Users/dskilton/conductor/workspaces/c64u/cancun/.context/NoBoundsSource/NoBounds/Link/StarWars/DISK-StarWars.prg build/SWDISK.PRG
tail -c +125 /Users/dskilton/conductor/workspaces/c64u/cancun/.context/NoBoundsSource/NoBounds/Music/MCH-SkyCaptain-0900.sid > build/SWMUSIC.PRG
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

echo "Built build/dhaka.prg"

C1541_BIN="$(command -v c1541 || true)"
if [[ -z "$C1541_BIN" && -x /Applications/vice-arm64-sdl2-3.9/bin/c1541 ]]; then
  C1541_BIN=/Applications/vice-arm64-sdl2-3.9/bin/c1541
fi

if [[ -n "$C1541_BIN" ]]; then
  rm -f build/dhaka.d64
  "$C1541_BIN" -format "dhaka,01" d64 build/dhaka.d64 \
    -write build/dhaka.prg DHAKA \
    -write build/SWCODE.PRG swcode \
    -write build/SWSCREEN.PRG swscreen \
    -write build/SWFONT.PRG swfont \
    -write build/SWTEXT.PRG swtext \
    -write build/SWSPRITES.PRG swsprites \
    -write build/SWBASE.PRG swbase \
    -write build/SWMUSIC.PRG swmusic \
    -write build/SWDISK.PRG swdisk >/dev/null
  echo "Built build/dhaka.d64"
else
  echo "c1541 not found; skipping D64 build"
fi

if command -v exomizer >/dev/null 2>&1; then
  exomizer sfx sys build/dhaka.prg -o build/dhaka_sfx.prg >/dev/null
  echo "Crunched build/dhaka_sfx.prg ($(stat -f%z build/dhaka_sfx.prg) bytes)"
else
  echo "exomizer not found; skipping crunched build (brew install exomizer)"
fi
