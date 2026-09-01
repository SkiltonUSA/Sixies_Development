# VZ200 Port Plan

The VZ200 port inherits the C64 repository, history, source artwork, exact
rules, and conformance vectors. It must not begin by translating raster or
bitmap code. The first deliverable is still a portable rules engine with
deterministic tests; the VZ200-specific work begins only after that boundary is
clean.

Keep Steve Olney's 1987 `VZ200/300 Assembly Language Programming Manual for
Beginners` and the VZ200 technical reference manual nearby while doing VZ
platform work. The Olney manual is especially useful for reading legacy VZ
assembly conventions, memory-loading patterns, screen access examples, and the
built-in editor assembler's pseudo-ops.
The attached `VZ200 Technical Reference Manual` is the primary hardware source
for the VZ200 side of this port. The attached `VZ300 Technical Manual` is
searchable and useful as a cross-check for shared VZ200/VZ300 behavior,
including the 6847 video interface, mode-selection latch bits, keyboard
handling, ROM helper routines, and memory-map differences between the machines.
P.C. Shaper's scanned guide `A Beginner's Guide to the VZ200/VZ300 Editor
Assembler` is also a useful legacy reference for the built-in editor-assembler
workflow. Treat it as supporting historical documentation; the copy attached in
this workspace is image-only, so it is not locally searchable without OCR.
Jason Oakley's Blue Bilby article `VZ200 & VZ300 - 8 bits of awesome!`
published on May 28, 2023 is also a useful quick overview of the machine
family, naming variants, common graphics color sets, and the broader VZ hobby
scene, but it should not replace the manuals for exact addresses or memory-map
decisions.
Oakley's Blue Bilby tutorial series `Developing for VZ200` parts 1 through 4,
published between October 25, 2019 and December 17, 2021, is also worth
keeping nearby as a practical snapshot of the current hobbyist toolchain:
`z88dk` builds, VS Code task wiring, VZEm usage, MPAGD support, TRSE support,
and Aseprite-based sprite export.
The attached `VZ300 Omnibus` and `VZ200 Giant Book of Games` are useful scanned
period references for examples and ecosystem context, but they are secondary
sources for this repository unless a concrete implementation detail needs to be
verified against a worked example.

## Target and toolchain

Target original VZ200 compatibility first, while being realistic about RAM.
The stock machine exposes 6 KB of user RAM and 2 KB of video RAM, with 16 KB
expansion extending RAM to `$cfff` according to the 1983 technical reference
manual. The initial playable target should assume a VZ200 with the 16 KB RAM
expansion or a VZ300-class memory budget. Treat a stock-6 KB build as a later
optimization milestone, not as the baseline requirement.

Use Z80 assembly for the hardware-facing port. Standardize new source on
`sjasmplus` rather than mixing assemblers:

- `CasperDev/vz-dis-dos` shows a commented VZ DOS disassembly that reassembles
  with `sjasmplus`.
- `CasperDev/vz-dis-games` adds commented VZ game disassemblies that also
  reassemble back to `.VZ` binaries with `sjasmplus`.
- `retroPrograms/VZ200` is useful as a small TASM-era example corpus, but it
  should remain reference material instead of defining the new build syntax.
- `WauloK/Millipede` is a larger game-sized reference with source, assets, and
  generated VZ outputs. Treat it as a layout and asset-pipeline example, not as
  a build standard.
- `zonared/vz-doom` is the strongest modern reference for repository shape: a
  hand-written Z80 project built with `sjasmplus`, optional Python generators,
  explicit `.VZ` wrapping, byte-exact simulator checks, and deliberate use of
  expansion RAM for larger data.

For graphics conversion, `WauloK/VZ200-Aseprite-Export` is useful for extracting
VZ-ready sprite or font data from indexed Aseprite sources. It is an asset
pipeline input, not the architecture for the game itself.

`gameblabla/flappybird_vz200` is useful for a different reason: it shows that a
mostly-C VZ game is viable, even on a non-expanded machine, but it also
documents practical drawbacks in this ecosystem such as weak platform docs,
slow naive sprite code, mono helper routines, and bitmap-mode sound quirks.
That supports this port's split: portable C for rules, assembly for the
performance-sensitive VZ200 layer.
`z88dk` remains a valid secondary path for prototypes and host-facing glue.
Blue Bilby's tutorials show a practical `zcc +vz` workflow, including VS Code
tasks and mixed C-plus-assembly builds. For this repository, that is useful
reference material, but it does not replace the primary `sjasmplus` plan for
the hardware-facing VZ200 build.

For emulation and packaging, prefer `.VZ` snapshots for fast iteration and WAV
cassette output only when testing loadability on real hardware. `bushy555`'s
repos are useful references for both formats and for MAME/MESS ROM setup.
`bushy555/VZ200-and-VZ300-demos` is additionally a good reference set for
rendering tricks, compression experiments, and mode-specific effects, but it
should inform presentation code only, never gameplay structure.

## Proposed module boundary

```text
ports/shared/
  include/sixies_rules.h
  src/sixies_rules.c
  tests/rules_test.c

ports/vz200/
  asm/main.asm
  asm/render.asm
  asm/input.asm
  asm/audio.asm
  asm/ui.asm
  asm/assets.asm
  tools/
  assets/
```

`sixies_rules.c` owns only fixed-size deterministic state and operations:

- 25 board bytes, score, piece, cursor, orientation, RNG, single-only, and
  game-over state
- piece generation and legal-placement queries
- commit, flood-fill, ordered chain resolution, and scoring
- ordered events such as piece placed, merge resolved, die upgraded, sixes
  cleared, single-only entered, and game over

The VZ200 assembly layer consumes that state or its events. Rendering, keyboard
scanning, speaker toggling, attract timing, and save/load packaging must never
change a rule result.

Use no dynamic allocation, recursion, floating point, or platform pointers in
the portable rules state. Keep flood fill iterative with fixed 25-byte queue
and visited storage, matching the C64 behavior.

## Video and layout

The VZ200's mode 1 graphics use the full 2 KB video RAM window at
`$7000-$77ff` for a 128x64 bitmap. The machine can only show one four-color set
at a time in this mode, so the dice cannot rely on six unique colors for their
identity. Shape and pip layout must carry the meaning; color can only reinforce
state.

Start with one compact board-plus-sidebar composition that keeps all 25 cells
visible:

```text
+-----------------------------+----------------+
| SCORE / STATUS              | SCORE          |
|                             | NEXT           |
| 5x5 BOARD                   | [die]          |
| 11x11 cells inside          | [die]          |
| a 56x56 playfield           | mode / prompt  |
|                             |                |
+-----------------------------+----------------+
```

Recommended first-pass layout:

- board origin near `(2,4)`
- cell pitch `11` with 1-pixel grid lines, for a `56x56` board footprint
- right sidebar width about `68` pixels for score, next piece, and status

Use mode 1 for the first playable milestone. Do not begin in text/lo-res mode
unless a later memory or rendering constraint forces it. The Wolfenstein demo
repo shows that mode 1 is practical on expanded-memory VZ200 systems, and that
compressed 6 KB variants are a separate engineering problem.

## Input and audio

Keep the keyboard controls behaviorally aligned with the C64 build where the
VZ keyboard allows it:

- `W`, `A`, `S`, `D`: move
- `Q` or `R`: rotate double
- `Space` or `Return`: place
- `N`: new game

Those keys exist in the published VZ200 keyboard matrix, so preserving the
control vocabulary is practical. Joystick support is optional until the game is
fully playable on keyboard.

Audio should start minimal. The hardware speaker is driven by the output latch,
with the speaker lines controlled by bits 0 and 5 in the technical manual's
documented cassette/speaker/VDC latch. First milestone audio can be limited to
simple placement, invalid-move, and merge cues. Music is explicitly later work.

## Milestones

## Current Strawman

`ports/vz200/asm/sixies.asm` is an expanded-RAM Mode 1 prototype assembled
with `sjasmplus` and wrapped by `scripts/package-vz200.py` as an autostarting
`build/vz200/SIXIES.VZ` snapshot. `make run-vz200` launches that snapshot in
the locally installed MAME VZ200 emulator using workspace-local ROM files.

It deliberately proves the visible and input-facing shape before the planned
portable C boundary: all 25 cells, generated singles/doubles, cursor movement,
rotation, placement, score, complete orthogonal flood-fill merges, chain
resolution, score saturation, and the origin-first double ordering. It uses a
fixed non-zero seed and does not yet emit the portable event stream or run the
platform-neutral JSON vectors. Treat it as a strawman, not as a conformant
port or an excuse to skip milestone 1.

The strawman currently keeps its code and stack in the stock VZ200 user-RAM
window, so it also boots without an expansion. The expanded-RAM requirement
remains the target for the future feature-complete port and its asset budget.

### 1. Portable rules engine

- Define `SixiesState` and an event stream in portable C.
- Implement the exact generator, placement, merge, scoring, and game-over
  behavior from `docs/game-rules.md`.
- Import every JSON vector into host-side tests.
- Pass the same tests without any VZ200 header or assembly dependency.

Acceptance: every vector passes, the rules source has no VZ200 hardware
dependency, and a saved state plus input produces identical state and events
across repeated host runs.

### 2. Expanded-RAM VZ200 playable board

- Add a `sjasmplus` build for a mode-1 playable board.
- Render the 5x5 grid, dice 1 through 6, score, next piece, cursor, and
  single-only indicator.
- Poll the keyboard and map the preserved controls.
- Show invalid placements distinctly without changing the rules.

Acceptance: a complete game can be played in VZ200 emulation with the 16 KB RAM
expansion, all 25 cells remain visible, and gameplay still matches the vectors.

### 3. Packaging and emulator workflow

- Emit a `.VZ` snapshot as the primary development artifact.
- Add a cassette WAV export path for real-hardware loading.
- Document the exact MAME/MESS ROM setup used by the port branch.
- Keep generated tables or derived assets checked in when that meaningfully
  reduces local tool requirements for a normal rebuild, following the approach
  used by `vz-doom`.

Acceptance: the game boots reproducibly in the chosen emulator workflow, and
the repository documents how to launch it from a clean machine.

### 4. Presentation and memory reduction

- Add speaker effects, attract screens, high-score UI, and settings/help flow.
- Convert source artwork into VZ-appropriate assets instead of raster-scaling
  C64 screenshots.
- Profile memory and investigate whether a stock-6 KB build is achievable.

Acceptance: the expanded-memory build is feature-complete, and any 6 KB effort
is treated as an explicit optimization project with measured tradeoffs.

## Technical decisions

- Retain the C64 8-bit RNG for deterministic vectors and comparable sessions.
- Preserve all RNG calls, including the unused second value for singles.
- Preserve origin-first resolution for doubles and active-cell chain anchors.
- Preserve score saturation at 9999 and strict-greater high-score insertion.
- Represent orientation with the same values `0` through `3`.
- Emit one merge event per consumed connected component, including value and
  group size, so presentation code can scale effects without inspecting or
  mutating rules internals.
- Do not depend on VZ DOS for gameplay. The DOS disassembly repo is reference
  material, not a runtime requirement.
- Standardize the new port's build on `sjasmplus`; use TASM sources only as
  syntax and layout references. Likewise, treat the Olney manual's built-in
  editor-assembler syntax and pseudo-ops such as `EQU`, `DEFB`, `DEFS`, and
  `DEFW` as legacy-reading aids, not as the new build contract.
- Prefer host-side generators and byte-exact verification for tricky rendering
  or table code before testing on hardware or in a full emulator.
- Treat the 16 KB expansion requirement as the default until measured memory
  usage proves otherwise. This is an engineering choice, not a claim that a
  smaller build is impossible.

## Port readiness checklist

Before beginning the port, run `make test-porting`, `make`, and `make crunch`
on the C64 branch. Review `docs/reference-assets.md` before converting art. If
the port reveals an ambiguous behavior, add a failing platform-neutral vector
and resolve it against the C64 implementation before writing a target-specific
workaround.

In a new branch or Conductor workspace, run `make setup-porting` first. It
locates the repository independently of the workspace name, verifies that the
handoff files and source masters are present, runs the vectors, and creates
`.context/porting-paths.env` with canonical absolute paths for local tools.
