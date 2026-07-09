# Wide Borders Framework

Small self-contained Commodore 64 demo built with ACME and intended to run in
VICE on macOS. It displays a static, centred RetroDNA logo in multicolour bitmap
mode while retaining a minimal split-raster framework that opens the lower
border.

The logo converter scales `.context/attachments/q2y3Hi/retro dna.png` onto a
320x200 canvas and creates a C64 multicolour bitmap. This supports four colours
per 4x8 cell, prioritising the source palette while retaining the logo's full
width. It is intentionally not a streamed or VSP effect.

## Build

```bash
./scripts/build.sh
```

This writes `build/wide_borders_framework.prg`. If `exomizer` is installed, the
build script also writes `build/wide_borders_framework_sfx.prg`.

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

The converter is [scripts/generate_retrodna_multicolor.py](scripts/generate_retrodna_multicolor.py).
The raster split and VIC-II setup live in `src/main.a`.
