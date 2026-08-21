# Sixies Agent Guide

This repository is the source of truth for the Commodore 64 game and for
future ports. Read this file, `docs/game-rules.md`, and the relevant porting
document before changing gameplay behavior.

## Build and verification

Requirements are bootstrapped locally where possible. Generated tools live in
`.tools/` and must not be committed.

```sh
make                 # build build/dice_merge.prg with ACME
make run             # build and launch in VICE
make crunch          # build build/dice_merge-crunched.prg with Exomizer 3.1.2
make music           # package the standalone Sixies SID tune
make test-porting    # validate the portable gameplay conformance vectors
make setup-porting   # verify and index a fresh branch/workspace
make setup-acme      # install the local ACME assembler
make setup-sidkit    # install the local c64SIDkit tools
make sidkit          # open the c64SIDkit sound-effect editor
```

ACME is always invoked with `--strict-segments`. A successful build with no
segment overlap is a required check for every C64 change.

Conductor runs `scripts/setup-porting-workspace.sh` for a new workspace. The
script discovers the Git root, verifies all specifications and source masters,
runs the conformance suite, and writes absolute path exports to the gitignored
`.context/porting-paths.env`. Source that file when a tool needs canonical
paths; never commit workspace-specific absolute paths.

## Repository architecture

- `src/grid_base.asm` owns startup, input, the 5x5 board model, piece
  generation, placement, flood-fill merging, raster scheduling, and the main
  loop.
- `src/assets/*.asm` owns UI pages, effects, scoring, high scores, sound,
  music integration, and generated data tables.
- `src/assets/*_master.*`, `src/assets/font/`, and
  `src/assets/exclamations/` contain source artwork. Binary, Koala, table, and
  preview outputs are generated from them by `scripts/` and `Makefile` rules.
- `src/music/` contains the standalone Sixies music source.
- `scripts/` contains asset converters, packers, font extraction, SID
  packaging, and local tool setup.
- `tests/porting/` is the platform-neutral behavioral contract. A port is not
  conformant until these vectors pass without platform-specific exceptions.
- `docs/reference/` contains selected, stable screen references. The complete
  source-art index is `docs/reference-assets.md`.

The C64 uses VIC bank 1, screen RAM at `$4400`, and bitmap RAM at `$6000`.
Hardware I/O and KERNAL remain visible with processor port value `$36`. The
current fixed regions are documented in `README.md`; individual modules also
declare fixed `* =` origins. Do not move one region without checking every
origin and rebuilding with strict segments. The assembled image currently
reaches `$cff8`, with late settings art beginning at `$ce00`.

Gameplay display is raster split into five board-row phases and one UI phase.
`board` is authoritative rules state. `renderBoard` is the IRQ-safe snapshot,
and `displayValues` is the board plus cursor preview. `boardUpdateInProgress`,
`boardDirty`, and `displayDirty` prevent an IRQ from observing partial state.

## Gameplay invariants

- Board storage is 25 row-major bytes. Zero is empty; values 1 through 6 are
  dice. Coordinates are zero-based and `index = y * 5 + x`.
- Connectivity is orthogonal only. Diagonal neighbors never join a group.
- A group is the complete connected component, and every component of at
  least three dice merges once regardless of whether it contains 3, 4, or
  more cells.
- Values 1 through 5 merge to one die of the next value at `activeIndex`.
  Value 6 groups disappear and do not leave a replacement.
- Chain reactions repeatedly resolve at the same active cell. For a double,
  the origin is fully resolved before the second cell is considered. If the
  second cell was cleared by the first resolution, it is skipped.
- A merge awards `group size * consumed die value`. Score arithmetic saturates
  at 9999.
- Spawn generation and its RNG-call order are part of game behavior. Do not
  reorder calls, the value-5 eligibility check, or the double-4 reroll.
- Once no orthogonally adjacent pair of empty cells remains, `singlesOnlyMode`
  becomes permanent for that game. Game over occurs when the resulting piece
  has no legal placement; in singles-only mode this means the board is full.
- Rules code must not depend on raster timing, sprites, SID state, animation,
  fonts, or C64 memory addresses. New ports should emit events and let their
  presentation layer consume them.

The exact turn lifecycle, RNG, and edge cases are specified in
`docs/game-rules.md` and executable in `tests/porting/validate_vectors.py`.
When implementation and prose disagree, first compare both with
`src/grid_base.asm`; then update code, docs, and vectors together.

## Controls

Gameplay keyboard controls are `W/A/S/D` to move, `R` or `Q` to rotate a
double, Space or Return to place, `N` for a new game, and the C64 key matrix
code `$3d` (shown as Tab by the host mapping) for Settings. Joystick port 2
uses directions and fire; hold fire and press left or right to rotate a double
counterclockwise or clockwise. Fire alone places when released. The `.` key
randomly fills the board and is a development-only endgame shortcut.

Moving down from the bottom board row focuses New Game for columns 0-2 or
Settings for columns 3-4. Left and right switch those controls, up returns to
the board, and place/fire activates the focused control. Settings uses
`W`/`S`, Space/Return, numbered menu shortcuts, `M` for its menu, and `X` to
close.

## Asset and change discipline

Edit source masters or converters, not generated `.bin`, `.kla`, `.asm`, PPM,
or preview output, unless the file is explicitly a hand-authored assembly
module. Run the narrow generator through `make`, inspect the generated preview,
then run the complete build.

Do not silently change game rules while tuning visuals. If behavior changes:

1. Add or update a conformance vector.
2. Run `make test-porting`.
3. Update `docs/game-rules.md`.
4. Build the normal and crunched C64 programs.

For the Game Boy work, follow `docs/porting-gameboy.md`. The first milestone is
a host-testable portable rules engine. The second is a simple monochrome board.
Animation, sound, title screens, mascot art, and presentation come afterward.
