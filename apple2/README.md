# Sixies for Apple II

This directory contains an Apple II port track for `SIXIES` that mirrors the original repo's workflow: source art stays in the main `src/assets/` tree, generated assets are rebuilt from scripts, and the Apple II target has its own build and setup path.

The Apple II version is a native `cc65` target. Gameplay uses mixed-mode hi-res, the title uses full-screen double hi-res, and game over uses mixed-mode double hi-res on an enhanced Apple IIe with auxiliary memory. It keeps the core rules of the C64 game:

- a 5x5 board
- random single or double dice
- rotating doubles
- merge-on-3 rules
- chain merges
- score by consumed face value, plus a 50-point bonus when sixes are removed
- C64-derived three-star merge fireworks and randomized monochrome comic callouts
- forced single-die mode once no adjacent empty pair remains
- game over when the last empty cell is filled in single-die mode

The Apple II graphics are rebuilt from the existing source images instead of copying C64 bitmap data directly. The asset converter quantizes the title and game-over art to the DHGR palette, serializes each scanline across main and auxiliary memory, and writes preview PNGs so the reduction can be reviewed without booting an emulator.

## Build

```sh
make -C apple2 setup-tools
make -C apple2
make -C apple2 disk
make -C apple2 run
```

The normal build creates:

- `apple2/build/SIXIES`: Apple II binary
- `apple2/build/sixies.po`: bootable ProDOS-order disk image
- `apple2/build/assets/*.MAIN`: generated DHGR main-memory pages
- `apple2/build/assets/*.AUX`: generated DHGR auxiliary-memory pages
- `apple2/build/previews/*.png`: nominal-color DHGR conversion previews

The packaged disk contains `SIXIES.SYSTEM`, `SIXIES`, and the four title/game-over DHGR bank files. In a ProDOS-aware Apple II emulator, launch `SIXIES.SYSTEM`.

`make -C apple2 run` builds the disk and boots it as drive 1 in an enhanced Apple IIe. The launcher copies the image to `apple2/build/emulator/` first, so emulator writes never alter the packaged build artifact.

## Tooling

`make -C apple2 setup-tools` prepares workspace-local tooling under `.tools/`:

- `.tools/apple2-venv`: Python environment with Pillow for asset conversion
- `.tools/applecommander`: AppleCommander jar for disk-image packaging
- `.tools/izapple2`: pinned universal macOS Apple IIe emulator
- `.tools/apple2-prodos`: pinned ProDOS 2.4.3 boot template
- Homebrew `openjdk` when the AppleCommander CLI needs a Java runtime and the keg is not already installed

The Apple II compiler tools come from `cc65`. This workspace already has `cc65` on `PATH`, but the Makefile checks it explicitly so the failure mode is direct.

## Development Loop

```sh
make -C apple2 doctor  # verify compiler, packaging tools, and emulator
make -C apple2 run     # rebuild, package, and boot SIXIES
make -C apple2 debug   # boot with ProDOS MLI tracing in the terminal
make -C apple2 clean   # remove generated program, disk, and converted art
```

Inside izapple2, press `F1` for emulator help, `F4` to toggle CPU tracing, `F5` to toggle full speed, `F6` to cycle display modes, and `F12` to save `snapshot.png`. The emulator boots a stock-style enhanced Apple IIe configuration with unnecessary expansion cards disabled.

## Controls

- Arrow keys or `W`, `A`, `S`, `D`: move the cursor
- `R` or `Q`: rotate a double piece
- `Space` or `Return`: place the current piece
- `N`: start a new game

The Apple II build currently prioritizes a playable core rules port and source-art reduction pipeline over C64-specific presentation effects such as raster animation, SID playback, and attract-mode page rotation.

A merge scores the face value of every consumed die: three ones score 3, three twos score 6, and so on. A six merge removes the dice and adds a 50-point bonus, so three sixes score 68. The earned points appear over the merge, travel to the left score panel, and then update its persistent five-digit total.

Technical notes collected from the Apple II graphics, game-development, and sound references used by this port are in [`docs/apple2-implementation-notes.md`](docs/apple2-implementation-notes.md).
