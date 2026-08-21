# Game Boy Port Plan

The Game Boy port inherits the C64 repository, history, source artwork, exact
rules, and conformance vectors. It must not begin by translating raster or
graphics code. The first deliverable is a portable rules engine that can run
on a host computer and on Game Boy hardware without conditional gameplay
behavior.

## Target and toolchain

Target original Game Boy (DMG) first, with Game Boy Color (CGB) support using
the same ROM and layout. Use GBDK-2020 and portable C for the game layer. Keep
the rules module free of GBDK headers so it can be compiled by a host C
compiler for fast tests. Emulicious is the primary debugger and SameBoy is the
second emulator used to catch timing and compatibility differences.

The Game Boy Advance is a separate future target. Do not add GBA-specific code
to the DMG/CGB port.

## Proposed module boundary

```text
ports/gameboy/
  include/sixies_rules.h
  src/rules.c
  src/game.c
  src/input.c
  src/render.c
  src/audio.c
  src/save.c
  tests/rules_test.c
```

`rules.c` owns only fixed-size state and deterministic operations:

- 25 board bytes, score, piece, cursor, orientation, RNG, single-only, and
  game-over state
- piece generation and legal-placement queries
- commit, flood-fill, ordered chain resolution, and scoring
- ordered events such as piece placed, group merged, die upgraded, sixes
  cleared, single-only entered, and game over

Rendering, input mapping, frame delays, particles, palette changes, sound,
music, screens, and save storage consume this state or its events. They must
never change a rule result.

Use no dynamic allocation, recursion, floating point, or platform pointers in
rules state. Use fixed-width integer types and caller-owned arrays. Keep flood
fill iterative with fixed 25-byte queue and visited storage, matching the C64
implementation.

## Screen layout

The Game Boy screen is 160 by 144 pixels. Preserve the C64's board-plus-sidebar
composition rather than shrinking a full 320 by 200 bitmap:

```text
+--------------------+----------+
| SCORE / STATUS     | SCORE    |
|                    | NEXT     |
|  5x5 BOARD         | [die]    |
|  20px cells        | [die]    |
|  100x100px         | mode/UI  |
|                    |          |
+--------------------+----------+
```

Place a 101 by 101 pixel grid near `(3,22)`, using five 20-pixel cells plus
grid edges. Use 16 by 16 die art centered inside each cell so lines remain
visible. Reserve the right-hand 52 pixels for a four-digit score, next-piece
preview, single-only indicator, and compact status. The mascot is not required
for the first playable milestone.

DMG uses four shades: black background, dark grid/shadow, light cursor, and
white die faces/pips as tile art allows. The cursor must distinguish valid and
invalid targets without relying on color. CGB may assign die palettes matching
the C64 artwork while preserving the identical tile geometry and rules.

Build the board as a background tilemap with reusable 8 by 8 tiles. Use sprites
only where they simplify cursor or effects; do not design the core board around
large per-cell sprite counts. Update changed cells rather than redrawing the
whole map every frame.

## Milestones

### 1. Portable rules engine

- Define a compact `SixiesState` and event stream.
- Implement the exact generator, placement, merge, scoring, and game-over
  behavior from `docs/game-rules.md`.
- Import every JSON vector into host-side tests.
- Add deterministic tests for complete turn sequences, not only helper calls.
- Pass the same tests under a host compiler and the Game Boy cross-compiler.

Acceptance: every vector passes, no rules source includes a Game Boy hardware
header, and a saved state plus input produces identical state and events on
host and target builds.

### 2. Monochrome playable board

- Render the DMG board, dice 1 through 6, score, next piece, and cursor.
- Map D-pad to movement, A to place, B to rotate, Start to New Game, and Select
  to Settings/pause.
- Show invalid overlap and out-of-bounds targets in a distinct monochrome
  pattern.
- Show single-only mode and a basic Game Over panel.

Acceptance: a complete game can be played in Emulicious and SameBoy, all 25
cells remain visible, double orientation is unambiguous, and gameplay results
still pass the portable vectors.

### 3. Persistence and complete UI

- Store five high scores and three-letter initials in cartridge SRAM.
- Add title, high-score, instructions/settings, credits, and attract flow.
- Add CGB palettes without changing the DMG-readable silhouettes.

### 4. Presentation parity

- Recreate placement and merge timing, callouts, shake, and fireworks using
  tile/sprite effects suited to Game Boy hardware.
- Adapt source artwork rather than downscaling C64 screenshots.
- Add sound effects, then arrange platform-appropriate music last.

The C64's Koala unpacking, raster splits, SID calls, and exact frame counts are
references for feel, not implementation requirements.

## Technical decisions

- Retain the C64 8-bit RNG for deterministic vectors and comparable sessions.
- Preserve all RNG calls, including the unused second value for singles.
- Preserve origin-first resolution for doubles and active-cell chain anchors.
- Preserve score saturation at 9999 and strict-greater high-score insertion.
- Represent orientation with the same values 0 through 3.
- Emit one merge event per consumed connected component, including value and
  group size, so graphics and audio can scale effects without inspecting or
  mutating rules internals.
- Use logical update ticks. Never tie rules progress to LCD scanlines, VBlank
  count, emulator speed, or an audio callback.
- Start with a fixed seed in tests; seed real games from timer and input jitter.
- Keep SRAM versioned and checksummed so later releases can migrate scores.

## Port readiness checklist

Before beginning the port, run `make test-porting`, `make`, and `make crunch` on
the C64 branch. Review `docs/reference-assets.md` before converting art. If the
port reveals an ambiguous behavior, add a failing platform-neutral vector and
resolve it against the C64 implementation before writing a target workaround.

In a new branch or Conductor workspace, run `make setup-porting` first. It
locates the repository independently of the workspace name, verifies that the
handoff files and source masters are present, runs the vectors, and creates
`.context/porting-paths.env` with canonical absolute paths for local tools.
