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

## Scope review

The C64 game has four distinct layers. They should be ported in this order so
presentation work cannot hide a rules regression:

| Layer | Required NES behavior | First shell |
| --- | --- | --- |
| Gameplay | 5x5 board, exact spawn RNG, single/double movement, rotation, placement, ordered merges, score saturation, singles-only transition, game over | Included |
| Product flow | New Game, title/attract loop, settings/instructions, five-entry high scores, initials, credits | New Game only |
| Feedback | Valid/invalid target, next piece, score, merge/chain feedback, game-over state | Native tile grid and dice; animation deferred |
| Presentation | Sixies font, dice art, mascot, callouts, wipes, shake, fireworks, music, sound effects | Deferred |

The development-only random board fill is useful for NES testing but is not a
shipping requirement. C64 raster splits, Koala packing, sprite multiplexing,
and SID register sequences are implementation references, not port scope.

The shell at `ports/nes/` establishes the complete controller-to-rules-to-
render loop. Its native PPU renderer uses a generated Sixies CHR set for the
5x5 lattice, dice, score, next piece, and valid or blocked placement states.
Run `make nes-test` for host rules checks and `make nes` for
`ports/nes/build/sixies-nes.nes`.

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

The rules module currently emits merge events directly in `SixiesState`.
Presentation code may consume `value`, `count`, `score_delta`, and `active`,
but it must not inspect temporary flood-fill storage or rerun a merge to decide
which effect to play.

## Cartridge and hardware strategy

Use NROM-256 for the rough shell: 32 KiB PRG ROM, 8 KiB CHR ROM, vertical
nametable mirroring, battery-backed PRG RAM, and the stock cc65 runtime. These
properties come directly from the generated iNES header. This is the smallest
useful target and keeps emulator and hardware diagnosis simple. The stock
linker layout assumes cartridge PRG RAM at `$6000-$7fff`; a prototype
cartridge or flash cart must provide it.

Do not commit the final release to NROM before converted art and audio have
been budgeted. At the end of the native-renderer milestone, measure PRG and
CHR use and choose one of these paths:

- Stay on NROM if the complete game fits without reducing source art quality.
- Move to MMC1/SxROM if title, callout, font, mascot, music, and save data need
  banked PRG/CHR plus battery-backed RAM. This is the expected production path.
- Use MMC3 only if later presentation genuinely requires scanline IRQs or more
  aggressive bank switching. Current gameplay does not justify it.

The board belongs in the background nametable. A 5x5 field made from reusable
dice and border tiles avoids the NES limit of eight sprites per scanline.
Sprites should be reserved for the cursor edge, mascot details, and short
celebration effects. Queue PPU updates during the main loop and apply them in
NMI; after the initial draw, update dirty cells and sidebar digits rather than
redrawing the full nametable.

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

### 0. Executable shell

- Build a valid NROM image with the installed cc65 toolchain.
- Display all 25 cells, score, next piece, mode, direction, and placement
  validity.
- Support D-pad movement, `A` placement, `B` rotation, and `Start` New Game.
- Exercise real spawning, merging, scoring, singles-only, and game-over logic.

Acceptance: `make nes-test` and `make nes` succeed and a controller can play a
complete game in an emulator. The rough-shell implementation and cold boot are
complete; a manual complete-game controller pass remains before closing the
milestone. Visual quality is intentionally not an acceptance criterion.

### 1. Portable rules engine

- Define a compact `SixiesState` and event stream.
- Implement the exact generator, placement, merge, scoring, and game-over
  behavior from `docs/game-rules.md`.
- Import every JSON vector into host-side tests.
- Pass the same tests under a host compiler and the NES cross-compiler.

Acceptance: every vector passes, no rules source includes NES hardware headers,
and a saved state plus input produces identical state and events on host and
target builds.

The shell has the platform-neutral module and representative host tests. The
remaining gate is to drive all canonical JSON vectors through the C module,
including complete state and ordered-event comparison, rather than maintaining
two manually selected test lists.

### 2. Playable NES board

- Render the board, dice 1 through 6, score, next piece, and cursor.
- Map the D-pad to movement, `A` to place, `B` to rotate, `Start` to New Game,
  and `Select` to Settings or pause.
- Show invalid overlap and out-of-bounds targets distinctly.
- Show single-only mode and a basic Game Over panel.

Acceptance: a complete game can be played on an NES emulator, all 25 cells
remain visible, double orientation is unambiguous, and gameplay results still
pass the portable vectors.

The console shell has been replaced with a native 5x5 tile grid and generated
Sixies CHR set. Valid, placed, and blocked targets have been exercised in
Nestopia UE. The remaining renderer work is a bounded NMI update queue, a final
art and layout pass, and stable reference captures. Keep NROM until that work
is complete so mapper changes cannot obscure PPU bugs.

### 3. Persistence and complete UI

- Store five high scores and three-letter initials in battery-backed save RAM
  when available, with a graceful RAM-only fallback for non-battery builds.
- Add title, high-score, settings, credits, and attract flow.
- Rebuild the typography and callouts from source artwork rather than from C64
  screenshots.

Define a versioned SRAM block with magic bytes and checksum before enabling
battery saves. Invalid or missing data must initialize the five-entry table;
it must never leak uninitialized cartridge RAM into names or scores.

### 4. Presentation parity

- Recreate placement and merge timing, callouts, shake, and fireworks with NES
  tile and sprite effects suited to the platform.
- Add sound effects first, then platform-appropriate music last.

Translate effect intent and duration, not C64 hardware operations. Schedule
all durations in logical 60 Hz NTSC frames, with PAL timing treated as a later
compatibility pass. Budget sprite-heavy fireworks against the eight-sprites-
per-scanline limit before converting their artwork.

## Delivery gates

Each milestone ends with the same checks: canonical rules vectors on the host,
a successful cc65 ROM link with a retained map file, a cold-boot emulator run,
and a ten-minute controller smoke test. Record ROM size, free PRG space, free
CHR space, worst-case NMI update bytes, and maximum sprite count. Mapper,
persistence, and audio decisions should be made from those measurements rather
than from the C64 memory map.

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
