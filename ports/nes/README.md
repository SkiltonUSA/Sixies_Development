# Sixies NES Port Workspace

This directory contains the first playable Nintendo NES shell and its portable
gameplay core. Its native tiled renderer reproduces the C64's 5x5 gray lattice,
value-colored dice, next-piece display, and legal or blocked placement states.
Animation, audio, save data, and complete menu flow remain later milestones.

Use `docs/porting-nes.md` as the milestone plan and `docs/game-rules.md` plus
`tests/porting/gameplay-vectors.json` as the gameplay contract.

`make setup-nes` creates the expected local directory layout:

- `ports/nes/build`
- `ports/nes/cfg`
- `ports/nes/include`
- `ports/nes/src`
- `ports/nes/tests`

Build and test it with:

```sh
make nes-test
make nes
make run-nes
```

The ROM is written to `ports/nes/build/sixies-nes.nes`. The build generates a
4 KiB native background pattern table at `ports/nes/build/sixies.chr` from
the supplied masters in `ports/nes/assets/dice/` using
`scripts/build-nes-chr.py`; cc65 supplies the cartridge's second 4 KiB pattern
table. The converter reduces the 64x64 RGBA exports to 24x24 NES-native dice
with normal, legal-preview, and blocked variants. The prototype uses the stock
cc65 NES runtime and NROM layout.
`make run-nes` opens it in the Nestopia UE emulator installed by
`make setup-nes`.

For general artwork, `scripts/convert-png-to-nes.py` emits CHR, compact
nametable, palette, metadata, and preview files from an 8-bit PNG. See
`docs/nes-graphics-converter.md` for its file contract, options, and NES palette
constraints. Its unit tests run as part of `make nes-test`.

Controller 1 maps the D-pad to cursor movement, `A` to placement, `B` to
clockwise rotation, `Start` to New Game, and `Select` to the placeholder UI
status. A legal target uses an inset marching border; a blocked target uses a
red and gray dithered die.

`src/rules.c` has no NES hardware dependency. Keep all board, RNG, placement,
merge, score, and game-over behavior there. `src/game.c` owns the PPU renderer
and controller loop without changing the rules.

Do not import C64 raster, bitmap, or SID code directly. Port behavior first;
recreate presentation with NES-native tiles, palettes, sprites, and APU code.
