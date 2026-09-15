# Sixies Bug Tracker

This ledger records reproducible defects, attempted fixes, confirmed root
causes, and verification. Do not mark a visual or timing bug closed solely
because the program assembles; verify it in one current VICE instance under
the triggering board state.

## Status key

- **Open**: reproducible and not corrected.
- **Verification**: corrected in code, but still awaiting a clean reproduction
  test or player confirmation.
- **Closed**: the original reproduction no longer fails and regression checks
  pass.
- **Reverted**: an attempted fix was removed because it changed intended
  behavior or did not address the root cause.

## Active bugs

### BUG-008: Board dice shrink or disappear during the Chain Reaction banner

- Status: **Closed**
- Date: September 7, 2026
- Area: gameplay raster multiplexer / Chain Reaction sprite ownership
- Symptoms: placed dice become smaller or disappear while the Chain Reaction
  artwork is visible.
- Reproduction: trigger a second-or-later merge while populated board rows are
  visible above and below the active cell.
- Expected: every board die retains its normal size and remains visible for the
  complete chain animation.
- Root cause: the 3x2 banner borrowed hardware sprites 2-7. Because board dice
  require sprites 0-4, its custom raster renderer intentionally skipped rows
  that overlapped the banner and cleared expansion state on shared board slots.
- Fix: compress the banner into a 3x1 native hi-res composite and assign it only
  to UI sprites 5-7 in the empty right panel. The normal five-row board renderer
  now continues throughout the chain pause without sharing sprite registers.
- Verification: a deterministic VICE capture filled all 25 cells while the
  banner was active; every die remained visible at native size and the banner
  stayed outside the grid. A second capture after the handoff retained all dice
  and restored the upcoming piece and both bottom controls.
- Regression checks:
  - all five populated board rows remain visible while the banner is active
  - board sprites 0-4 retain their X/Y positions and expansion state
  - banner remains white and clear of the board and upcoming dice
  - bottom controls return after the banner
  - strict-segment ACME build
- Related files: `scripts/build-chain-reaction-sprite.py`,
  `src/assets/chain_reaction_sprite.asm`

### BUG-007: Screen contracts during a chain reaction

- Status: **Closed**
- Date: September 7, 2026
- Area: chain-reaction presentation / VIC-II display mode
- Symptoms: the visible gameplay screen briefly contracts horizontally when a
  chain reaction reaches its second or later merge.
- Reproduction: trigger any placement that resolves at least two consecutive
  merge groups.
- Expected: the bitmap, grid, and border geometry remain fixed throughout the
  chain reaction.
- Root cause: the chain-only impact effect called `RunMergeGridShake`, which
  animated the low three fine-scroll bits of `VIC_MODE` (`$d016`). Moving the
  bitmap viewport against the fixed VIC-II border made the screen edges appear
  to shrink.
- Fix: chain-level effects no longer invoke the viewport-shake routine. Chain
  sounds, scoring, banner, particles, and dice animations remain unchanged.
- Verification: a VICE monitor regression invoked the second-or-later chain
  effect entry point with the normal 40-column `$d016` value and confirmed the
  register was identical on return. The normal and crunched builds and all 34
  portable gameplay vectors also pass.
- Regression checks:
  - `VIC_MODE` stays unchanged through second-and-later merge effects
  - chain banner and particle effects still run
  - strict-segment ACME build
- Related files: `src/assets/merge_chain_sounds.asm`,
  `src/assets/merge_shake.asm`

### BUG-001: Board sprite row disappears while moving the hover dice

- Status: **Verification**
- Area: gameplay raster multiplexer
- First known occurrence: August 2026; recurred September 6, 2026
- Symptoms: moving or rotating the hover piece can make a complete row of
  committed board dice disappear. The bitmap grid lines remain present and
  the dice return after moving again.
- Trigger: the fourth or fifth board row has several active sprites while a
  two-die preview or side-panel sprites are also being multiplexed.
- Historical root cause: the board-row renderer missed the VIC-II sprite
  Y-start deadline when preview DMA and a worst-case five-sprite row consumed
  its setup window. The renderer was shortened, fixed X positions were moved
  to initialization, and the schedule was given a sprite-retirement gap.
- Current recurrence: side-panel control setup was later inserted before the
  fourth board-row render. That work consumed the timing margin restored by
  the historical fix.
- Current fix: render the fourth board row before retargeting sprites 6-7 to
  the side controls. Enabling the controls now preserves active board sprites
  0-4 instead of replacing the full VIC-II enable mask.
- Verification on September 6, 2026: a monitor-driven VICE stress case filled
  all 25 cells, continuously moved an invalid double across board rows 1-4,
  and sampled six separate raster phases. Every capture retained nonzero
  sprite pixels in all five rows; only the intended dithered hover moved.
- Regression checks:
  - strict-segment ACME build
  - full five-die row plus two-die hover movement
  - repeated movement across rows 3-5
  - only one VICE instance running the current PRG
- Related files: `src/grid_base.asm`,
  `src/assets/bottom_icon_control.asm`

Attempt history:

1. Delayed display publication to the UI IRQ. **Reverted** because the earlier
   context showed synchronous publication was intentionally added to prevent
   a one-frame ghost lag; it did not fix this row loss.
2. Kept committed dice visible instead of showing the gray invalid hover.
   **Reverted** because it removed required placement feedback and did not fix
   the raster failure.
3. Rebuilt and relaunched without first finding the timing regression.
   **Unsuccessful**; build success does not validate sprite deadlines.

## Closed and reverted bugs

### BUG-006: Bottom control icons jump into the merge effect

- Status: **Closed**
- Date: September 7, 2026
- Area: merge-effect and side-control sprite ownership
- Symptoms: during a merge, New Game or Settings briefly appeared near the
  mascot or board instead of remaining at the bottom of its side panel.
- Reproduction: trigger a merge firework while its three particles cross the
  upper or middle display.
- Expected: particle sprites retain their artwork and coordinates; bottom
  controls return only after the effect releases the sprites.
- Root cause: `fireworkActive` covered both the one-sprite score flight and the
  three-sprite particle burst. The bottom-control raster correctly shared
  sprites 6-7 with the score flight, but incorrectly did the same during the
  particle burst, replacing effect pointers and coordinates mid-frame.
- Fix: use state 1 for the shareable score flight and state 2 for the particle
  burst. Bottom-control setup returns without touching sprites 5-7 while state
  2 is active; the firework completion restores state 0.
- Verification: a held-state VICE capture retained all three star sprites and
  suppressed both control icons throughout repeated UI raster phases. A full
  effect run then restored New Game and Settings at their bottom positions.
- Regression checks:
  - three-sprite burst retains all effect pointers and coordinates
  - controls remain available during the single-sprite score flight
  - controls return at their bottom positions after the burst
  - strict-segment ACME build
- Related files: `src/assets/bottom_icon_control.asm`,
  `src/assets/merge_firework_code.asm`

### BUG-005: Board columns shift and overlap after a chain merge

- Status: **Closed**
- Date: September 7, 2026
- Area: Chain Reaction sprite handoff
- Symptoms: after a chain merge, dice in the center and right board columns
  shifted left; lower-row dice could appear doubled or overlap another column.
- Reproduction: trigger a Chain Reaction banner, let it disappear, then leave
  dice visible in board columns 2-4.
- Expected: every die remains centered in its original grid cell.
- Root cause: the 3x2 banner borrows hardware sprites 2-7 and rewrites their X
  registers. The board renderer restores pointer, color, and Y on every row,
  but its timing optimization initializes board X registers only at startup.
  Banner sprites 2-4 therefore retained their composite X positions after the
  handoff.
- Fix: restore the fixed `BoardSpriteX` coordinates for sprites 2-4 inside the
  interrupt-disabled banner hide path, before normal raster rendering resumes.
- Verification: a deterministic VICE test ran a complete banner show/hide,
  then rendered committed dice in all three borrowed columns plus a centered
  vertical hover double. Columns 2-4 remained distinct and both filled and
  inverse preview phases stayed centered.
- Regression checks:
  - chain show/hide followed by dice in columns 2-4
  - vertical double remains centered in column 2 through both blink phases
  - strict-segment ACME build
- Related file: `src/assets/chain_reaction_sprite.asm`

### BUG-004: Vertical double flashes both dice in one cell

- Status: **Closed**
- Date: September 7, 2026
- Area: gameplay raster multiplexer / Chain Reaction sprite handoff
- Symptoms: while moving a vertical double, both hover dice intermittently
  appeared in the same board cell during the normal/inverse blink.
- Reproduction: start normal gameplay, rotate the offered double vertically,
  and move it across adjacent board rows.
- Expected: both halves blink together in their separate origin and second
  cells.
- Root cause: the six-sprite Chain Reaction renderer added a helper call to
  every normal board-row IRQ. The added cycles consumed the timing margin
  needed to retarget a hardware sprite between adjacent rows, leaving its old
  position visible for part of the blink.
- Fix: the normal IRQ again calls `RenderBoardRow` and `SetupBottomSprites`
  directly with their original cycle count. `ShowChainReactionSprite` patches
  only those two JSR targets while the banner is active; the hide path restores
  them atomically before gameplay resumes.
- Verification: deterministic VICE captures exercised filled and inverse
  vertical-double blink phases before and after a complete banner show/hide.
  Both dice retained separate adjacent-row positions, and the Chain Reaction
  composite continued to render away from the merge.
- Regression checks:
  - strict-segment ACME build
  - vertical double moved across all adjacent board-row pairs
  - normal and inverse blink phases keep distinct Y positions
  - Chain Reaction show/hide restores the normal raster targets
- Related files: `src/grid_base.asm`,
  `src/assets/chain_reaction_sprite.asm`

### BUG-002: Gray invalid-hover feedback removed

- Status: **Reverted**
- Date: September 6, 2026
- Cause: an attempted workaround for BUG-001 stopped occupied cells from
  alternating with their gray dithered preview.
- Resolution: restored the intended gray invalid-hover behavior. This was not
  the cause of the disappearing row.

### BUG-003: Verification used multiple stale VICE windows

- Status: **Closed**
- Date: September 6, 2026
- Symptoms: screenshots and manual checks could sample different builds.
- Cause: repeated `make run` calls left more than one workspace emulator open.
- Resolution: terminate only the workspace's existing VICE processes before a
  final visual test, then launch one current PRG and confirm the process list.

## New bug template

```markdown
### BUG-NNN: Short title

- Status: **Open**
- Date:
- Area:
- Symptoms:
- Reproduction:
- Expected:
- Root cause:
- Fix:
- Regression checks:
- Related files:
```
