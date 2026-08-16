# Nintendo NES Port Plan

The NES port inherits the C64 repository, history, source artwork, exact
rules, and conformance vectors. It must not begin by translating VIC-II or SID
code. The first deliverable is a portable rules engine that runs identically
under a host compiler and the NES toolchain.

## Target and toolchain

Target the NTSC NES first. Use `cc65`, `ca65`, and `ld65` for the production
build, and keep the rules module free of NES headers so it can be compiled by a
host C compiler for fast tests. Keep rendering, input, and audio in the NES
layer; keep generator, placement, merge, scoring, and game-over behavior in a
platform-neutral rules layer.

The repository bootstrap exposes the toolchain through `make setup-nes`, which
verifies the commands on `PATH`, creates `ports/nes/`, and records canonical
paths in `.context/nes-toolchain.env`.

## Proposed module boundary

```text
ports/nes/
  include/sixies_rules.h
  src/rules.c
  src/game.c
  src/ppu.c
  src/input.c
  src/audio.c
  src/save.c
  cfg/sixies.nes.cfg
  tests/rules_test.c
```

`rules.c` owns only fixed-size deterministic gameplay state:

- 25 board bytes, score, piece, cursor, orientation, RNG, single-only, and
  game-over state
- piece generation and legal-placement queries
- commit, flood fill, ordered chain resolution, and scoring
- ordered events such as piece placed, group merged, die upgraded, sixes
  cleared, single-only entered, and game over

Rendering, controller mapping, animation delays, palette updates, music, sound
effects, title flow, and save persistence consume rules state or rules events.
They must never change a gameplay result.

Use no dynamic allocation, recursion, floating point, or platform pointers in
rules state. Use fixed-width integer types and caller-owned arrays. Keep flood
fill iterative with fixed 25-byte queue and visited storage.

## Screen layout

The NES visible area is 256 by 240 pixels. Preserve the C64 board-plus-sidebar
composition instead of stretching or screenshot-converting the full C64 frame:

```text
+-------------------------+-------------+
| SCORE / STATUS          | SCORE       |
|                         | NEXT        |
|  5x5 BOARD              | [die]       |
|  32px cells             | [die]       |
|  160x160px playfield    | mode/UI     |
|                         |             |
+-------------------------+-------------+
```

Keep all 25 cells visible at once. Reserve the right sidebar for score,
next-piece preview, single-only indicator, and compact prompts. The mascot is
optional for the first playable milestone and can return once the port is
functionally correct.

Build the board from nametable tiles. Use sprites only where they simplify the
cursor, dice highlights, or celebratory effects. Do not design the core board
around large per-cell sprite counts.

## Milestones

### 1. Portable rules engine

- Define a compact `SixiesState` and event stream.
- Implement the exact generator, placement, merge, scoring, and game-over
  behavior from `docs/game-rules.md`.
- Import every JSON vector into host-side tests.
- Pass the same tests under a host compiler and the NES cross-compiler.

Acceptance: every vector passes, no rules source includes NES hardware headers,
and a saved state plus input produces identical state and events on host and
target builds.

### 2. Playable NES board

- Render the board, dice 1 through 6, score, next piece, and cursor.
- Map the D-pad to movement, `A` to place, `B` to rotate, `Start` to New Game,
  and `Select` to Settings or pause.
- Show invalid overlap and out-of-bounds targets distinctly.
- Show single-only mode and a basic Game Over panel.

Acceptance: a complete game can be played on an NES emulator, all 25 cells
remain visible, double orientation is unambiguous, and gameplay results still
pass the portable vectors.

### 3. Persistence and complete UI

- Store five high scores and three-letter initials in battery-backed save RAM
  when available, with a graceful RAM-only fallback for non-battery builds.
- Add title, high-score, settings, credits, and attract flow.
- Rebuild the typography and callouts from source artwork rather than from C64
  screenshots.

### 4. Presentation parity

- Recreate placement and merge timing, callouts, shake, and fireworks with NES
  tile and sprite effects suited to the platform.
- Add sound effects first, then platform-appropriate music last.

The C64 raster schedule, Koala unpacking, and SID calls are references for
feel, not implementation requirements.

## Technical decisions

- Retain the C64 8-bit RNG for deterministic vectors and comparable sessions.
- Preserve all RNG calls, including the unused second value for singles.
- Preserve origin-first resolution for doubles and active-cell chain anchors.
- Preserve score saturation at 9999 and strict-greater high-score insertion.
- Represent orientation with the same values 0 through 3.
- Emit one merge event per consumed connected component, including value and
  group size, so graphics and audio can scale effects without inspecting or
  mutating rules internals.
- Use logical update ticks. Never tie rules progress to PPU scanlines, NMI
  count, emulator speed, or an audio callback.
- Start with a fixed seed in tests; seed real games from timer and controller
  jitter.

## Port readiness checklist

Before beginning the port, run `make test-porting`, `make`, and `make crunch`
on the C64 branch. Review `docs/reference-assets.md` before converting art. If
the port reveals ambiguous behavior, add a failing platform-neutral vector and
resolve it against the C64 implementation before writing a target workaround.

In a new branch or Conductor workspace, run `make setup-porting` and
`make setup-nes` first. They verify the source contract, validate the vectors,
check the C64 baseline, verify the NES toolchain, and record canonical paths in
the gitignored `.context` files.
