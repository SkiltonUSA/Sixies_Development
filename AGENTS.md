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
make probability-table # regenerate exact piece-generation probabilities
make test-porting    # validate the portable gameplay conformance vectors
make setup-porting   # verify and index a fresh branch/workspace
make setup-acme      # install the local ACME assembler
make setup-sidkit    # install the local c64SIDkit tools
make sidkit          # open the c64SIDkit sound-effect editor
make gimp            # open GIMP for source-master artwork editing
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
  generation orchestration, placement, flood-fill merging, raster scheduling,
  and the main loop. `src/spawn_probability.asm` owns the fixed weighted deal
  table and single-required neighbor-match bonus in the `$3dd0-$3ecf` code gap.
- `src/assets/*.asm` owns UI pages, effects, scoring, high scores, sound,
  music integration, and generated data tables.
- `src/assets/new_game_icon_master.png` is the generated New Game control's
  source art; `settings.asm` retains the original hand-authored gear sprite.
  `bottom_labels.asm` contains the compact labels, and
  `bottom_icon_control.asm` raster-multiplexes both icons beside the board.
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
reaches `$cff8`, with late settings art beginning at `$ce00`. The region
`$4c00-$4d7f` is reserved for runtime preview/title/effect sprites and must
never contain persistent code or asset data. Gameplay uses `$30/$31` for
inverse previews, `$32/$33` for invalid dithered previews, and `$34` for the
animated merge score.
Only the visible bitmap bytes `$6000-$7f3f` may be cleared. The unused tail
`$7f40-$7fff` contains preview-sprite utility code and must survive screen
transitions.

Gameplay display is raster split into five board-row phases and one UI phase.
`board` is authoritative rules state. `renderBoard` is the IRQ-safe snapshot,
and `displayValues` is the board plus cursor preview. `boardUpdateInProgress`,
`boardDirty`, and `displayDirty` prevent an IRQ from observing partial state.
Only a valid, uncommitted cursor preview alternates between filled and inverse
sprite silhouettes; committed board dice never blink.
The gameplay board begins at bitmap character row 3, leaving two character
rows plus a spacer for the centered light-green wordmark bitmap. New Game and
Settings are side-panel controls and must not be moved back under the board.

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
- A merge awards `3 * consumed die value * chain multiplier`, regardless of
  group size. Chain multipliers are 1, 2, 5, 10, 20, and 40, capped at 40,
  and continue across origin-first and second-cell resolution for doubles.
  Eliminating value-6 dice adds a separate 150-point bonus. Score arithmetic
  saturates at 9999.
- Spawn generation and its RNG-call order are part of game behavior. The fixed
  39-entry weighted deal table rejects RNG bytes 235-255 and maps accepted
  bytes 1-234 with `(byte - 1) modulo 39`; do not reorder that process.
- `docs/piece-probabilities.md` is generated from the portable spawn oracle;
  run `make probability-table` after an intentional generator change.
- Before every draw, `singlesOnlyMode` is recomputed from the current board.
  With no orthogonally adjacent pair of empty cells, only the single entries
  with weights 5, 3, and 1 are eligible. A later merge can restore doubles.
  Game over occurs when the resulting piece has no legal placement.
- While a single is required, an exact 10% bonus roll replaces the generated single
  with the value of one uniformly selected occupied cell orthogonally adjacent
  to any blank. Candidate cells are unique, not counted once per blank edge.
- While a value-5 die and a blank are both present, each visible generated 2
  gets one exact 5% roll to become a 4. This runs after doubles are forced to a
  single and before the single-required neighbor bonus.
- Rules code must not depend on raster timing, sprites, SID state, animation,
  fonts, or C64 memory addresses. New ports should emit events and let their
  presentation layer consume them.

The exact turn lifecycle, RNG, and edge cases are specified in
`docs/game-rules.md` and executable in `tests/porting/validate_vectors.py`.
When implementation and prose disagree, first compare both with
`src/grid_base.asm`; then update code, docs, and vectors together.

## Controls

Gameplay keyboard controls are `W/A/S/D` to move, `Q` to rotate a double
counterclockwise, `E` to rotate it clockwise, Space or Return to place, `N`
to request a new game, and `O` for Settings. A gameplay New Game request,
including the focused side control, shows `Y OR N TO CONFIRM`; `Y` clears the
current game and `N` cancels. Joystick port 2
uses directions and fire; hold fire and press left or right to rotate a double
counterclockwise or clockwise. Fire alone places when released. The `.` key
randomly fills the board and is a development-only endgame shortcut.

On attract-mode and post-game high-score pages, `Space` or `N` starts a new
game. A qualifying score must finish its three-letter initials entry before
these keys regain their start-game behavior.

Moving down from the bottom board row focuses New Game for columns 0-2 or
Instructions for columns 3-4. Left and right switch those controls, up returns
to the board, and place/fire activates the focused control. Instructions opens
the Settings pages, which use
`W`/`S`, Space/Return, numbered menu shortcuts, `M` for its menu, and `X` to
close.

## Asset and change discipline

Edit source masters or converters, not generated `.bin`, `.kla`, `.asm`, PPM,
or preview output, unless the file is explicitly a hand-authored assembly
module. Run the narrow generator through `make`, inspect the generated preview,
then run the complete build.

GIMP 3 is the supported interactive editor for raster source masters. Use
`make gimp GIMP_ASSET=path/to/master.png` to open one from the repository, but
keep all resizing, palette conversion, packing, and preview generation in the
deterministic scripts.

Do not silently change game rules while tuning visuals. If behavior changes:

1. Add or update a conformance vector.
2. Run `make test-porting`.
3. Update `docs/game-rules.md`.
4. Build the normal and crunched C64 programs.

For the Game Boy work, follow `docs/porting-gameboy.md`. The first milestone is
a host-testable portable rules engine. The second is a simple monochrome board.
Animation, sound, title screens, mascot art, and presentation come afterward.
