# Bangalore Star Wars Scroller Intro

Standalone C64 Star Wars scroller intro inspired by Raistlin's write-up and
the Nobounds / Genesis Project StarWars part.

The primary `build/bangalore.prg` target is a native ACME port of the
technique from the NoBounds StarWars part (`StarWars.cpp` in the public
release): a hires-bitmap crawl with real pixel-level perspective.
`scripts/generate_tables.py` builds a 16x16 font from a small set of unique
16px row segments, precomputes bit-picked FontData tables for every
(screen line, byte, source column) the perspective mapping needs, and emits a
fully unrolled plotter. At runtime the scrolltext streams through 16 cyclic
256-byte column buffers as font-row indices; the plotter samples them with
`ldy ScrollData+col,x / lda FontData_a,y / and FontData_b,y / sta bitmap`,
skipping more source rows per screen line near the horizon. Background is
1-bits and ink is 0-bits, so overlapping glyph halves combine with `AND`.

`build/bangalore-loader.prg` (written to the D64 as `BANGALORE`) is an
alternative path that loads the vendored, original Nobounds-generated part
from disk, phase-locks CIA2 Timer B for its stable raster code, and jumps
into the original StarWars entry point at `$9fcc`.

Build:

```bash
./scripts/build.sh
```

Build a Sparkle2 packaging script and, when Mono or Wine is available, a
Sparkle-linked D64:

```bash
make sparkle
```

Run in VICE, when installed:

```bash
./scripts/run.sh
```

The default run path autostarts `build/bangalore.prg`, the self-contained
native bitmap scroller.

To test the packaged D64 loader for the original Nobounds-generated part:

```bash
RUN_D64=1 ./scripts/run.sh
```

Output:

- `build/bangalore.prg` -- native bitmap perspective scroller (default run target)
- `build/bangalore-sparkle-part.prg` -- Sparkle2 payload, assembled at `$080d`
- `build/bangalore-loader.prg` -- D64 loader for the original Nobounds part
- `build/bangalore-direct.prg` -- monitor-preload runner for the original part
- `build/bangalore-lite.prg` -- older character-mode comparison build
- `build/bangalore-lite_sfx.prg` -- crunched comparison build when `exomizer` is available
- `build/bangalore.d64`
- `build/bangalore.sls` -- Sparkle2 loader script
- `build/bangalore-sparkle.d64` -- Sparkle2 disk, when Sparkle2 can run locally

Sparkle2 support:

- `scripts/ensure_sparkle2.sh` clones or updates `https://github.com/SkiltonUSA/Sparkle2.git` under `.context/Sparkle2`.
- `scripts/generate_sparkle_sls.py` writes a Sparkle Loader Script for `build/bangalore-sparkle-part.prg`.
- `scripts/build_sparkle.sh` runs the normal build, prepares `build/bangalore.sls`, and invokes Sparkle2 through `mono` or `wine` when either is installed.
- Mono is the preferred non-Windows runner. Wine on macOS can launch Sparkle2 but may exit without writing a D64; in that case use the generated `build/bangalore.sls` with Sparkle2 on Windows.

Vendored Nobounds assets:

- `src/assets/starwars/swcode.prg`
- `src/assets/starwars/font.bin`
- `src/assets/starwars/text.bin`
- `src/assets/starwars/screen.bin`
- `src/assets/starwars/sprites.bin`
- `src/assets/starwars/basecode.prg`
- `src/assets/starwars/music.prg`
- `src/assets/starwars/disk.prg`
