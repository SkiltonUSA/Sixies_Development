# Sixies for Atari 8-bit

This directory contains a native 6502 assembly port of Sixies for the Atari
8-bit family. The supported profiles are the 64K Atari 800XL and the 128K
Atari 130XE. A stock original Atari 400/800 is a 16K-48K machine, so it is not
the machine meant by the 64K/128K targets in this port.

The game is a playable first native port: piece generation, placement,
orthogonal merging, chains, scoring, game over, keyboard/joystick input,
instructions, converted artwork, POKEY cues, XEX packaging, and a bootable ATR
are implemented. The 130XE build detects extended RAM at runtime and caches the
7.75K title framebuffer in an extended bank. Both targets use one XEX.
Cursor movement, rotation, placement, and merge animation use dirty-region
updates, so the ornate gameplay grid is not decompressed or blanked during
normal play.
The startup presentation flows from the title to the instruction screen and
requires a new continue press before the first game begins.

## Quick start on macOS

From an existing checkout:

```sh
make -C atari8 setup-tools
make -C atari8 doctor
make -C atari8 run64
make -C atari8 run128
```

For a fresh checkout:

```sh
git clone https://github.com/SkiltonUSA/Sixies_Development.git
cd Sixies_Development
git switch Sixies-C64-Game-Beta
make -C atari8 setup-tools
make -C atari8 doctor
```

The setup script installs or verifies Homebrew, cc65 (`ca65` and `ld65`),
Exomizer 3, Atari800, Python, and Pillow. It builds `dir2atr`, `adir`, and
`ataricom` from a pinned AtariSIO revision and installs the supplied XL/XE ROM
under the gitignored `.tools/atari8/` directory after verifying its SHA-256.
No ROM is committed to the repository.

The tool choices follow the native formats: cc65's Atari target emits XEX
segments and a RUN vector, Exomizer's `-t168` mode creates a self-extracting
Atari executable, AtariSIO creates and inspects ATR images, and Atari800 runs
both XL and XE machine profiles.

## Build outputs

| Command | Output |
| --- | --- |
| `make -C atari8` | `build/sixies.xex` |
| `make -C atari8 crunch` | `build/sixies-crunched.xex` |
| `make -C atari8 disk` | `build/sixies.atr` |
| `make -C atari8 test` | XEX contract, rules, memory-path, and asset tests |
| `make -C atari8 doctor` | Complete build, tests, compression, ATR, and format checks |

The ATR is a 90K single-density PicoBoot406 disk containing the crunched XEX.
The raw XEX remains useful for fast emulator iteration and debugger labels are
written to `build/sixies.lbl`.

## Controls

| Input | Action |
| --- | --- |
| Joystick 1 or `W/A/S/D` | Move the piece |
| `Q` or `E` | Rotate a pair |
| Fire, `Space`, or `Return` | Start/place/continue |
| `I` | Instructions |
| `M` | Toggle POKEY audio |
| `N` | New-game confirmation or Start from title |
| `Y` / `N` | Confirm/cancel a new game |

The launcher assigns Atari800's second keyboard-joystick layout (`W/A/S/D`) to
joystick port 2, which the game reads alongside the physical/USB joystick on
port 1. The native Atari `CH` keyboard path remains enabled as well. This avoids
SDL consuming the host letters before the Atari OS can report them.

## Graphics and assets

The selected playfield is ANTIC mode F (OS GRAPHICS 8): 320x192, one bit per
pixel. It gives Sixies the same sharp monochrome intent as the C64 high-resolution
board and Apple II DHGR art, works consistently on NTSC and PAL displays, and
leaves 80-pixel sidebars around the 160-pixel board. The display list restarts
screen DMA at `$9000`, because an ANTIC mode-F line may not cross a 4K boundary.

`scripts/generate_assets.py` converts the shared source masters at build time:

- supplied Apple II DHGR A2FM title, decoded and reference-verified before
  scaling its complete 560x192 composition to ANTIC F;
- the high-resolution 5x5 grid master and its complete Apple DHGR game-screen
  counterpart, reference-verified and cropped into the Atari board geometry;
- Apple Studio313 presentation and illustrated Game Over masters, converted
  into centered Atari-native screens;
- the supplied boxed instruction-screen design, rebuilt at 320x192 with Atari
  64K/128K labels and the complete WASD/joystick control legend;
- shared Sixies font;
- supplied C64 bitmap and screen-map mascot validation, with the compact
  high-score mascot master reduced to 80x100 so its eyes, mouth, two dice,
  gloves, and shoe details survive in the Atari sidebar;
- supplied ACME assembly dice sprites, centered into Atari 32x24 cells;
- all ten official exclamation-word masters—Awesome, Boom, Dang, Fives,
  Let's Go, Sixies, Whoa, Wow, Yeah, and Yes—slightly enlarged and inverted
  into a white-on-black native Atari callout atlas;
- the supplied four-point merge star, flashed with XOR at the resolved die;
- an Atari-native invalid-placement overlay plus diagonal shading that
  identifies the occupied cell beneath a hovering piece;
- ASCII-indexed 8x8 glyph data for the bitmap text renderer.

The generated binaries and PNG inspection atlases are kept in `build/` rather
than committed. Full-screen title, presentation, instructions, Game Over, and
gameplay-grid art use a small 6502 PackBits-style decoder, reducing their
in-memory footprint while writing directly to the 31-page ANTIC framebuffer.
SID and Apple speaker byte streams are hardware-specific, so
their cues and musical intent are translated into native POKEY pitch envelopes
and a compact title phrase in `src/sound.s`.

See [docs/architecture.md](docs/architecture.md) for the graphics alternatives,
memory map, boot strategy, reference projects, and prioritized assembly
improvements. See [RULES_README.md](RULES_README.md) for the implemented game
rules and current parity boundary.

## Repository and Conductor integration

The port lives in this existing GitHub repository rather than splitting shared
art and rule sources into another repository. `.github/workflows/atari8.yml`
builds, tests, crunches, and uploads both XEX variants. Repository-level
Conductor scripts provide Build Atari, Test Atari, Run Atari 64K, and Run Atari
128K actions. Shared Conductor settings become available to all workspaces once
they are merged into the repository's default branch.

## Tool and format references

- [cc65 Atari target documentation](https://cc65.github.io/doc/atari.html)
- [Atari800 downloads and documentation](https://atari800.github.io/download.html)
- [AtariSIO disk-image tools](https://github.com/HiassofT/AtariSIO)
- [Exomizer project home](https://bitbucket.org/magli143/exomizer/wiki/Home)
- [130XE banked-memory map](https://www.atariarchives.org/mapping/appendix16.php)
- [AtariAge discussion of bootable assembly disks](https://forums.atariage.com/topic/241044-writing-asm-programs-that-boot-from-disk/)
