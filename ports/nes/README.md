# Sixies NES Port Workspace

This directory is the home for the Nintendo NES port. Keep the gameplay rules
portable and deterministic first, then attach the NES-specific presentation
layer.

Use `docs/porting-nes.md` as the milestone plan and `docs/game-rules.md` plus
`tests/porting/gameplay-vectors.json` as the gameplay contract.

`make setup-nes` creates the expected local directory layout:

- `ports/nes/build`
- `ports/nes/cfg`
- `ports/nes/include`
- `ports/nes/src`
- `ports/nes/tests`

Do not import C64 raster, bitmap, or SID code directly into this directory.
Port behavior first; recreate presentation with NES-native code later.
