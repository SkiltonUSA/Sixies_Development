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

### BUG-014: Completed initials corrupt the high-score start prompt

- Status: **Verification**
- Date: September 16, 2026
- Area: post-game high-score sequence
- Symptoms: after entering the third high-score initial, fragments of `ENTER
  INITIALS` and the entered letters remain beneath `SPACE OR N START`, making
  the prompt appear corrupted.
- Reproduction: finish with a qualifying score, enter all three initials, and
  observe the prompt drawn immediately afterward.
- Expected: the initials-entry message is removed completely before the start
  prompt appears.
- Root cause: the completion path called `DrawHighScorePage` directly. That
  routine redraws the table and new prompt but does not clear the bitmap rows
  previously occupied by the two-row initials message and typed letters.
- Fix: reset and clear the high-score hires page after the third initial, then
  redraw the completed table and start prompt on a clean bitmap.
- Regression checks:
  - enter three initials for a qualifying score
  - no `ENTER INITIALS` or typed-letter pixels remain behind the start prompt
  - the completed name remains in the high-score table
  - strict normal and crunched builds
- Related file: `src/assets/high_scores.asm`

### BUG-013: Chain Reaction callout missing on some second or third merges

- Status: **Verification**
- Date: September 16, 2026
- Area: double-piece chain presentation
- Symptoms: the Chain Reaction image appears for cascades at one cell but can
  be absent when the second or third merge is resolved from the other die of a
  placed double.
- Reproduction: place a double whose origin produces a merge, then whose
  second cell produces the next merge in the same placement chain.
- Expected: every merge numbered 2 or higher displays the Chain Reaction
  callout before its merge animation.
- Root cause: the callout was invoked only after an upgraded die formed
  another group at the same active cell. The chain multiplier correctly
  continued into the double's second cell, but that transition entered the
  merge routine below the callout trigger.
- Fix: move the callout trigger to the shared confirmed-group entry. It now
  checks the existing chain depth before every merge, covering same-cell
  cascades and origin-to-second-cell transitions without showing before the
  first merge.
- Verification: a production-path VICE regression placed a `1+3` double. The
  origin formed merge #1, then the second cell formed merge #2 at a different
  active index; execution stopped immediately after the real callout renderer
  and the supplied Chain Reaction image was visible in the sidebar. Strict
  normal and crunched V1.050 builds and all 45 portable vectors pass. V1.051
  is running in VICE for player confirmation.
- Regression checks:
  - first merge has no Chain Reaction callout
  - same-cell second and third merges each show the callout
  - a second-cell merge after an origin merge shows the callout
  - strict normal and crunched builds
- Related files: `src/grid_base.asm`,
  `src/assets/chain_reaction_sprite.asm`

### BUG-012: Music does not restart at game over

- Status: **Verification**
- Date: September 16, 2026
- Area: game-over audio lifecycle
- Symptoms: with the default gameplay music setting of OFF, the game-over
  animation and screen remain silent.
- Reproduction: leave gameplay music OFF and play until no legal placement
  remains.
- Expected: the title tune restarts from its beginning as soon as the
  game-over sequence begins, independently of the gameplay music preference.
- Root cause: `AnimateGameOver` used the preference-aware gameplay music
  initializer, so the default OFF setting suppressed game-over music.
- Fix: game over now uses the unconditional presentation-music initializer.
  That initializer explicitly stops any current playback and initializes the
  tune again, ensuring game over always starts at the beginning.
- Verification: strict normal and crunched V1.041 builds and all 45 portable
  gameplay vectors pass. V1.042 is running in VICE for audible confirmation.
- Regression checks:
  - game over restarts music when gameplay music is OFF
  - game over restarts music from the beginning when gameplay music is ON
  - a new game reapplies the gameplay music preference
  - strict normal and crunched builds
- Related files: `src/grid_base.asm`, `src/assets/bottom_controls.asm`

### BUG-011: Gameplay sound effects are silent by default

- Status: **Verification**
- Date: September 16, 2026
- Area: title-to-game SID handoff
- Symptoms: the new-game ripple begins audibly, then subsequent movement,
  placement, and merge effects are silent with the default audio settings.
- Reproduction: launch a fresh build, start from the title page, and move the
  offered piece without changing Options.
- Expected: title music plays on the title page; gameplay music is OFF and
  Sound FX are ON by default.
- Root cause: two SID lifecycle faults occurred when gameplay music was OFF.
  The title-music stop routine cleared `$d418`, leaving master volume at zero.
  Once that was corrected, the startup ripple exposed a second fault: its
  physical voice-1 gate remained ON, while later effects changed the gate only
  in their software shadow before publishing the final ON state. With no real
  OFF-to-ON transition, the SID envelope could not retrigger.
- Fix: stopping title music preserves the initialized master volume. Each new
  effect now writes its gate-off state to the physical SID before publishing
  its final gate-on registers, and effect completion releases voice 1 whenever
  gameplay music is inactive.
- Verification: strict normal and crunched V1.038 builds and all 45 portable
  gameplay vectors pass. V1.039 is running in VICE for audible confirmation.
- Regression checks:
  - default `audioMode` is `AUDIO_SFX_ONLY`
  - title tune begins on the title page
  - title tune stops when default gameplay begins
  - startup ripple releases voice 1 when its animation completes
  - repeated movement effects retrigger, not only the first effect
  - movement, invalid-placement, setup, and merge effects remain audible
  - strict normal and crunched builds
- Related files: `src/assets/title_music.asm`,
  `src/assets/bottom_controls.asm`

### BUG-010: Gameplay music preference silences the title tune

- Status: **Verification**
- Date: September 16, 2026
- Area: title/attract music lifecycle
- Symptoms: the title and attract pages are silent when gameplay music uses
  its intended default setting of OFF.
- Reproduction: launch a fresh build and wait for the title page without first
  changing the Options music setting.
- Expected: the SID title tune starts when the title page appears. The OFF
  preference silences music only after gameplay begins; sound effects remain
  enabled.
- Root cause: `InitTitleMusic` applied the global gameplay music-disable bit to
  attract mode, so the same default that muted gameplay also prevented title
  initialization.
- Fix: title and attract pages now use an unconditional music initializer.
  Leaving attract mode or starting a new game reapplies the gameplay setting,
  stopping and clearing the SID when gameplay music remains OFF.
- Verification: strict normal and crunched V1.038 builds and all 45 portable
  gameplay vectors pass. V1.039 is running in VICE for audible confirmation.
- Regression checks:
  - title tune begins when the title page appears
  - default gameplay begins without background music
  - gameplay Sound FX remain enabled
  - enabling gameplay music in Options starts the tune
  - returning to an attract title always restores title music
- Related files: `src/grid_base.asm`, `src/assets/bottom_controls.asm`,
  `src/assets/settings_screen.asm`

### BUG-009: Chain Reaction callout appears absent or corrupt

- Status: **Closed**
- Date: September 16, 2026
- Area: Chain Reaction artwork conversion / presentation
- Symptoms: the sprite could appear missing, malformed, or visually corrupt
  when a populated board triggered a real second merge.
- Reproduction: create three connected 2s that merge beside two existing 3s,
  causing the upgraded 3 to merge again.
- Expected: the white Chain Reaction words are clearly visible in the same
  right-sidebar panel used by merge exclamations, without covering dice or the
  score.
- Root cause: the effect was forced through a three-sprite, Y-expanded
  rendition even though the existing exclamation system already provided a
  stable 72-by-64 bitmap panel. Expansion, sprite priority, and colorful art
  beneath the sprite all made the supplied lettering fragile.
- Fix: replace the hardware-sprite renderer with a packed bitmap callout. The
  converter now samples the original pale-green callout directly from the
  supplied master, turns it white while retaining the original black outline
  and lettering as transparent detail, scales it proportionally to 64 by 32
  pixels, and centers it in the existing 72-by-64 merge-callout panel. The
  established decoder,
  screen colors, and right-sidebar coordinates present and clear it while the
  upcoming dice and bottom controls retain normal sprite ownership.
- Verification: a production-path VICE regression in build V1.016 resolved a
  2-to-3 merge that immediately formed a second group. The callout appeared
  cleanly beneath the upcoming dice while the score, complete board, preview,
  mascot, and bottom controls remained intact.
- Regression checks:
  - real `ResolveAtActiveIndex` chain reaches the banner
  - callout remains readable in the right-sidebar exclamation panel
  - active dice and permanent score remain unobscured
  - strict-segment ACME build
- Related files: `scripts/build-chain-reaction-sprite.py`,
  `src/assets/chain_reaction_sprite.asm`

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
- Fix: the initial correction reduced the effect to UI sprites 5-7. Build
  V1.011 removes Chain Reaction sprite ownership completely and presents it
  through the existing right-sidebar bitmap callout panel. The normal board,
  preview, and control renderers now continue without a chain-specific sprite
  handoff.
- Verification: a production-path VICE capture exercised a real second merge.
  Every die remained visible at native size, the upcoming piece and bottom
  controls stayed present, and the bitmap callout remained outside the grid.
- Regression checks:
  - all five populated board rows remain visible while the banner is active
  - board sprites 0-4 retain their X/Y positions and expansion state
  - white bitmap callout appears beneath the upcoming dice
  - upcoming piece and bottom controls remain present during the pause
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
