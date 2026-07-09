# Cancun C64 Demo

Small self-contained Commodore 64 demo built with ACME and intended to run in
VICE on macOS. The effect stack is deliberately simple and dependency-light:
a custom-charset filled sine wave in the style described by Nurpax, a pulsing
title, and a bottom-row text scroller.

## Build

```bash
./scripts/build.sh
```

This writes `build/cancun.prg`. If `exomizer` is installed, the build script
also writes `build/cancun_sfx.prg`. The filled-wave lookup tables and charset
are regenerated automatically from `scripts/generate_filled_sine.py` before the
assembly step.

## Run in VICE

```bash
./scripts/run.sh
```

The run script assembles the demo, launches VICE if it can find an `x64sc` or
`x64` binary on this Mac, and serves the `build/` directory on a local HTTP
port for Conductor.

## Tooling

- `brew install acme`
- `brew install exomizer` (optional, for the crunched artifact)
- Install VICE.app in `/Applications`, or put `x64sc` / `x64` on `PATH`

Reference:

- https://nurpax.github.io/posts/2018-06-07-c64-filled-sinewave.html
