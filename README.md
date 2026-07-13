# Bangalore Star Wars Scroller Intro

Standalone C64 Star Wars scroller intro inspired by Raistlin's write-up and
the Nobounds / Genesis Project StarWars part.

The primary `build/bangalore.prg` target is now a disk loader for the real
Nobounds-generated pixel plotter. It vendors the generated code and data files
needed by the part, loads them from `build/bangalore.d64`, phase-locks CIA2
Timer B for the stable raster code, and jumps into the original StarWars entry
point at `$9fcc`.

The earlier compact character-mode recreation is still built as
`build/bangalore-lite.prg` for comparison, but it is not the main target because
it cannot reproduce the pixel-level perspective compression.

Build:

```bash
./scripts/build.sh
```

Run in VICE, when installed:

```bash
./scripts/run.sh
```

The default run path preloads the StarWars assets through the VICE monitor and
jumps directly to the part. This avoids the very slow standard runtime disk
loads that otherwise look like a freeze after `RUN`.

To test the packaged D64 loader instead:

```bash
RUN_D64=1 ./scripts/run.sh
```

Output:

- `build/bangalore.prg`
- `build/bangalore-direct.prg`
- `build/bangalore.d64`
- `build/bangalore-lite.prg`
- `build/bangalore-lite_sfx.prg` when `exomizer` is available

Vendored Nobounds assets:

- `src/assets/starwars/swcode.prg`
- `src/assets/starwars/font.bin`
- `src/assets/starwars/text.bin`
- `src/assets/starwars/screen.bin`
- `src/assets/starwars/sprites.bin`
- `src/assets/starwars/basecode.prg`
- `src/assets/starwars/music.prg`
- `src/assets/starwars/disk.prg`
