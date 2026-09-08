# Sixies for Game Boy

This directory is the development foundation for the native Sixies port. It
currently builds a hardware-valid ROM with the native 5x5 Sixies game grid; the
C64, Apple II, Atari, and NES implementations remain the gameplay references
while the Game Boy port is developed.

## Target

- Original Game Boy and Game Boy Color compatible ROM
- GBDK-2020 C and SM83 assembly, with RGBDS available for low-level tools
- MBC5 cartridge, automatic ROM sizing, 8 KiB battery-backed SRAM
- 160x144 display, 8x8 tiles, four-shade DMG-safe visual baseline
- Centered 5x5 board with 24x24-pixel cells and rail-style intersections

MBC5 leaves room for banked graphics, music, and code. Battery-backed SRAM is
reserved for settings and the high-score table.

## Installed toolchain

| Tool | Role | Installation |
| --- | --- | --- |
| GBDK-2020 4.5.0 | SDCC compiler, SM83 assembler/linker, Game Boy libraries | Pinned under `.tools/gameboy/` |
| `png2asset` | PNG tile, tilemap, palette, and metasprite conversion | Included with GBDK |
| `romusage` | ROM/RAM bank usage checks | Included with GBDK |
| RGBDS | Standalone assembler, linker, `rgbgfx`, and ROM-header utilities | Homebrew |
| SameBoy | Primary accuracy and debugger emulator | Homebrew cask |
| mGBA | Independent compatibility emulator | Homebrew cask |
| Tiled | Tilemap and level-layout editor | Homebrew cask |
| hUGETracker 1.0.11 | Game Boy music composition and `uge2source` export | Pinned under `.tools/gameboy/` |

The setup script verifies SHA-256 checksums for downloaded GBDK and hUGETracker
archives. GBDK supports Apple Silicon, Intel macOS, x86-64 Linux, and ARM64
Linux. Desktop authoring applications are installed only on macOS; CI uses the
same pinned Linux compiler.

## Setup

From the repository root:

```sh
make -C gameboy setup
make -C gameboy doctor-desktop
make -C gameboy test
make -C gameboy run
```

Conductor runs the setup automatically for a new workspace and exposes Build,
Test, Doctor, SameBoy, and mGBA commands. The scripts do not depend on an
interactive shell profile.

The first hUGETracker launch may require Control-clicking the app and selecting
Open because its upstream macOS build is unsigned. On Apple Silicon it also
uses Rosetta 2. The compiler and ROM build are native Apple Silicon binaries.

## Commands

| Command | Result |
| --- | --- |
| `make -C gameboy` | Build `gameboy/build/sixies.gb` and debug symbols |
| `make -C gameboy test` | Validate cartridge metadata/checksums and print bank use |
| `make -C gameboy run` | Build and launch in SameBoy |
| `make -C gameboy run-mgba` | Build and launch in mGBA |
| `make -C gameboy music` | Open the repository-local hUGETracker |
| `make -C gameboy clean` | Remove generated Game Boy build output |

SameBoy is the primary emulator because it supports DMG, Game Boy Color, Super
Game Boy, accurate timing, symbols, breakpoints, watchpoints, backtraces, and
reverse stepping. In SameBoy, enable **Developer Mode** and open the debugger
console. Load `gameboy/build/sixies.sym` when source symbols are needed. Always
cross-check releases in mGBA and, before publishing, on physical DMG and GBC
hardware using a compatible flash cartridge.

## Asset and audio workflow

- Draw backgrounds and sprites on an 8x8 grid with the four DMG shades.
- Use Tiled for tilemap layout and export source PNGs into `assets/`.
- Convert committed PNG sources with GBDK's `png2asset`; commit sources and
  conversion scripts, not generated build output.
- Compose four-channel music in hUGETracker and export C with `uge2source` for
  hUGEDriver/GBDK integration.
- Keep gameplay readable without color first, then add optional GBC palettes.

## GitHub

`.github/workflows/gameboy.yml` runs on pushes, pull requests, and manual
dispatch. It downloads the checksum-pinned Linux GBDK package, performs a clean
build, validates the ROM header and checksums, reports bank usage, and uploads
the ROM plus `.map`, `.noi`, and `.sym` debugging files as the
`sixies-gameboy` artifact.

No proprietary Nintendo SDK, copyrighted boot ROM, or emulator BIOS is needed.
