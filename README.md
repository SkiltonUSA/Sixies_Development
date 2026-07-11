# Wide Borders Framework

Small self-contained Commodore 64 demo built with ACME and intended to run in
VICE on macOS. It displays a static, centred RetroDNA logo in multicolour bitmap
mode, raster-splits to an inverted character-mode filled sine wave above the
logo, then switches back to a normal filled sine wave below it while retaining a
lower-border opening.

The logo converter scales `.context/attachments/q2y3Hi/retro dna.png` onto a
320x200 canvas and creates a C64 multicolour bitmap. This supports four colours
per 4x8 cell, prioritising the source palette while retaining the logo's full
width. The sine waves use the precomputed filled-segment charset approach from
Nurpax's breakdown: https://nurpax.github.io/posts/2018-06-07-c64-filled-sinewave.html

## Build

```bash
./scripts/build.sh
```

This regenerates the sine lookup tables and RetroDNA bitmap data, then writes
`build/wide_borders_framework.prg`. If `exomizer` is installed, the build script
also writes `build/wide_borders_framework_sfx.prg`.

## Run in VICE

```bash
./scripts/run.sh
```

The run script assembles the framework, launches VICE if it can find an
`x64sc` or `x64` binary on this Mac, and serves the `build/` directory on a
local HTTP port for Conductor.

## Tooling

- `brew install acme`
- `brew install ffmpeg` (for the RetroDNA bitmap converter)
- `brew install exomizer` (optional, for the crunched artifact)
- Install VICE.app in `/Applications`, or put `x64sc` / `x64` on `PATH`

The logo converter is [scripts/generate_retrodna_multicolor.py](scripts/generate_retrodna_multicolor.py).
The sine generator is [scripts/generate_filled_sine.py](scripts/generate_filled_sine.py).
The raster split and VIC-II setup live in `src/main.a`.
