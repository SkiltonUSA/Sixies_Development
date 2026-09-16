# Atari/C64 to Game Boy port review

## Scope and reference hierarchy

The Atari 800XL branch's current `atari8/RULES_README.md` and
`atari8/src/rules.s` define gameplay, probability, progression, and scoring.
The C64 and Atari presentation assets and their shared title tune define the
visual/audio identity. Where older computer versions differ in rules, the
revised Atari rules win; this is not a port of an obsolete probability table.

This is native GBDK C/SM83 code, not a binary translation of 6502 machine code.
The original Game Boy strawman had gameplay and some converted art, but lacked
the complete attract sequence, credits, top ten/initials, and pause settings.
These now run in the native cartridge alongside the revised rules.

## Source-to-port comparison

| Area | Source | Game Boy implementation |
| --- | --- | --- |
| Rules, RNG, deal weighting | `atari8/src/rules.s`, `atari8/RULES_README.md` | `src/game.c`: connected groups, ordered resolution, shared chain depth, bonuses, 16-bit score, independent unlocks, pressure and rescue |
| Title / attract / credits | `atari8/src/credits.s` | `src/main.c`, `src/presentation.c`: 11-second cards and manual credits shortcut |
| High scores | `atari8/src/high_scores.s` | `src/scores.c`, `src/storage.c`: same ten defaults, strict-greater insertion, three initials, battery journal |
| Effects and HUD | Atari rules/presentation routines | `src/ui.c`: score and next panel, ripple, shake, flash, stars, awards, chain badges, callouts, audio cues |
| Title art | `gameboy/assets/title_master.png`, supplied as `title_screen-Main.png` | `src/generated_screens.c`: the native 160x144 composition is palette-mapped without geometric resampling; other wordmarks retain their separate source |
| Start menu | `gameboy/assets/start_menu_master.png`, supplied as `Sixies_Menu_New160x144.png` | Bank 4 artwork with dynamic highlight and cursor for Play, Settings, How to Play, and High Scores; opens after title confirmation and on results Main Menu; settings persist to SRAM |
| Results menu | `gameboy/assets/results_menu_mockup.png`, supplied as `Game_Over_New_moddified_160x144_New.png`; clean template retained as `results_master.png` | Native 160x144 layout with a dedicated muted-green palette and two-option arrow menu; live five-digit Score/Best fields use reserved tiles 240-254 in bank 6; follows the original Game Over splash after 90 frames or A/B |
| Studio intro | `gameboy/assets/intro_master.png` supplied at native resolution | Four-second startup splash with its embedded four-color palette and A/Start skip |
| Title palette | Four colors embedded in the supplied native logo | One palette spans the complete title to prevent visible 8x8 color boundaries; colors are reduced to the CGB's native 5-bit channels |
| UI font | `gameboy/assets/font_itty_bitty_master.png`, supplied Ittiest Bittiest Clean Variable D atlas | Single-color ASCII glyphs are sampled directly from their native 8x8 cells without antialiasing or resampling |
| Title prompt font | `gameboy/assets/fonts/morbidosa/Morbidosa_avr.bmp`, Roberto Mocci, SIL OFL 1.1 | Native 8x8 glyphs compose `Press Start` at (36, 116); ten transparent sprites skip the space, preserving the hardware scanline limit; immediately visible, then 30 frames on/30 frames off; license bundled alongside the unmodified fonts |
| Credits logo | `atari8/assets/credits_logo_master.png` | Banked 96x24 credits logo |
| High-score screen | Supplied `highscore160x144.png`, stored as `assets/highscore_master.png` | Native full-screen header/mascot/panel, five entries per page, three editable initials and full 16-bit scores; existing ten-entry battery saves preserved |
| Dice | Six native `assets/dice/*_18x18.png` assets; faces 1, 2 and 5 rebuilt by their `scripts/rebuild-*-die.py` scripts using shared `scripts/dice_frame.py` | Unscaled 18x18 canvases inside 20x20 cells with one-pixel insets; face 1 matches the exact three-face silhouette and bevel, while faces 2 and 5 use the four-face frame. Rebuilds have solid 3x3 pips without extra padding. Normal/highlight/invalid states and all four Next orientations are supported |
| Invalid-placement preview | `gameboy/assets/invalid_placement_master.png`, supplied as `M_Fall_55x52.png` | A rejected A press triggers the sound and a 19-VBlank falling-mascot overlay in the 48x48 Next frame; no hover/rotation or muted trigger; shares only background preview tiles 15-46 and restores the cached normal preview when the sound ends |
| Grid | `gameboy/assets/grid_layout_master.png` | Sampled green rails and rounded board corners; locked 100x100 board at (5, 22), with a clean, separate preview frame at (109, 78); legacy connector and tab removed |
| Ten comic callouts | `apple2/assets/merge_*_master.png` | AWESOME, BOOM, DANG, FIVES, LETS GO, SIXIES, WHOA, WOW, YEAH, YES; one dynamic 48x16 slot |
| Chain banner | `atari8/assets/chain_reaction_master.png` | Master letter crops reflowed into 48x16 sidebar art |
| Star | `src/assets/merge_firework_sprite.asm` | Shared C64 sprite reduced to one 8x8 OAM tile |
| Game-over illustration | `apple2/assets/game_over_master.png` | 160x104 illustration plus score and continuation prompts |

The Apple II master directory holds shared high-resolution Sixies art reused
across ports; those masters are converted directly rather than copying a
low-resolution computer framebuffer. No assets/code from commercial Game Boy
games or the supplied Nintendo manuals were incorporated.

## Correctness findings addressed

- Crowded-board rolls now use the Atari's actual 1-in-2 and 3-in-4 decisions,
  preserving the subsequent random-roll sequence rather than substituting a
  percentage roll. No-adjacency matching does not consume a density roll.
- Matching weights aggregate in ascending face order, counting every empty
  neighboring edge; seed initialization includes the original RNG warm-up.
- Five-only progression remains independent: clearing four sixes before the
  four milestone unlocks single 5 and 4+5, not single 4 or 3+4. The Atari
  assembly's contiguous index approach has this corner-case defect; the port
  follows the written independent-milestone rule rather than reproducing it.
- New pieces reset to the center/right-facing cursor, as in Atari, rather than
  silently relocating to an available placement. Invalid placements do not
  mutate the board, score, or random state; game-over placement is rejected.
- Initials, pause selections, and instruction pages update in place. Reloading
  all tiles on each button press previously dropped short inputs and blanked
  the display. Instruction transitions also clear the entire old text width.
- Gameplay caches cells; moving the cursor no longer reloads the full tile
  atlas or screen. Chain multipliers use OAM rather than leaving text trails.
- Settings now uses `gameboy/assets/settings_master.png` with Itty Bitty option
  text, no footer caption, and Left=OFF/Right=ON controls. FLASH OFF selects
  reduced flashing. Eight visual states share a lossless 224-tile atlas in bank 4;
  only the options tilemap updates during input. DMG/CGB tests compare every pixel
  in all eight states, check unchanged-value/held-input saves, and reboot with
  persisted sound/flash preferences.
- High-score/settings saves use a versioned CRC-16 record with two alternating
  slots and commit-last writes. The previous single best-score save migrates.
- Pause uses `gameboy/assets/pause_master.png` with Itty Bitty live labels and
  the original menu actions. Bank 5 holds a shared, lossless tile atlas; cursor,
  sound and flash updates change only small tilemap regions. DMG/CGB tests check
  all twenty selection/preferences combinations against the converted template,
  preserve the paused board/score, and verify returns from Instructions and
  cancelled New Game confirmation without stale artwork.

## Hardware adaptations, not exact reproductions

### Dice-effect parity follow-up

The Atari routines in `src/main.s` (`service_animation_input`) and
`src/graphics.s` (`draw_piece_preview`, `toggle_merge_ripple_step`,
`run_merge_grid_shake`, `flash_six_clear`, `run_merge_star_firework`) were
compared against the Game Boy UI. The following differences are now addressed:

- Reduced flashing also disables the high-face grid shake.
- Occupied preview cells use a steady diagonal hatch; empty partners keep blinking,
  with the same hatch at the visible origin when a pair extends off-grid.
- Five ripple steps clamp inward from the actual board edges to the merge
  origin; fives and sixes include diagonal arms, without duplicate toggles.
- Animation waits retain the latest fresh movement or clockwise-rotation input
  for the next piece, never placement. Held A cannot place a second piece.
- Stars use the Atari's nine-step rise/fall and sideways-offset tables with
  two VBlanks per step, clipped to the Game Boy display rather than wrapping.
  Six-clear palette inversion also uses five VBlanks.

DMG and CGB regression tests check steady hatch pixels, blinking empty partners, all four
off-grid orientations, reduced-flashing suppression, edge/center ripple states,
star coordinates at center and corners, and brief buffered input during merges.
The approved 20x20 cells, 18x18 dice canvases, 19-frame invalid mascot/sound, and nonblocking
one-second chain badge are preserved. This is behavioral parity, not identical
wall-clock timing: tile uploads and the Game Boy refresh rate differ from Atari.

### Retained platform differences

The C64 award animation in `src/assets/merge_chain_sounds.asm` has also been
adapted: outlined points appear above the merged die, pause three frames, move
diagonally into the score panel, and update its displayed total on arrival.
Movement is scaled to four-pixel horizontal and vertical steps,
with a two-frame landing hold. Game Boy preserves its own full award calculation
(bonuses and chain multipliers), supports five digits, and uses a stationary
popup in reduced-flashing mode. No score is awarded twice or deferred in the
game rules; only presentation of the already-calculated total waits for landing.

- Display: 160x144 with 8x8 tiles and an 20x20-per-cell board replaces the larger
  computer framebuffer. The 5x5 grid fills 100x100 pixels; the logo, HUD,
  instructions, and credits are reflowed.
  Lettering uses a compact native bitmap font; title branding is original art.
- Color: DMG is four-shade; CGB uses eight four-color title/game-over palettes.
  A single gameplay palette keeps dice and selection states readable.
- Effects: only consumed fives/sixes shake the grid, with two two-pixel
  right-and-back cycles. Board tiles shift inside their existing canvas without
  clearing or relocating the tilemap; the score, Next window and boundary stay fixed.
  three OAM stars replace XOR framebuffer particles. Ripples and high-face
  timing are native adaptations, not cycle-identical computer effects.
- Music: the title/attract loop is a compact hUGETracker conversion of the
  user-provided `We are the Reason` MIDI. Its rights holder is unverified, so it
  must only be distributed where music rights are cleared. The public-domain
  hUGEDriver is built into ROM0 and reads the bank-3 song during VBlank; it
  stops before menus and gameplay so native sound effects retain the hardware
  channels.
- Persistence uses cartridge SRAM rather than computer disk I/O. Saved settings
  are additional accessibility/convenience features; in-progress games are not
  saved. Reduced flashing is optional; full effects remain the default.

## Memory and reproducibility

The 128 KiB MBC5 ROM places fixed game/UI code in bank 0, tile data in bank 1,
full-screen art in bank 2, available space in bank 3, and presentation code in
bank 4. Gameplay uses 175 resident background tiles: the 253-tile source atlas keeps
all callouts in ROM, loading only the current one into its 12-tile VRAM slot.
Full-screen conversion asserts the DMG tile-count limit and emits CGB attribute
maps. Generated files are checked in for compiler-only builds.

Run `make assets` inside `gameboy` after installing `setup-assets`. Pillow is
pinned. GitHub checks regenerated output against the checked-in files before
building, so changing a shared art master cannot silently leave the cartridge
artwork stale.

## Validation performed and remaining release gates

- Host rules tests: 100,000-deal sampling, opening/pressure weights, crowded
  rescue, weighted matching, isolated holes, all rotations/bounds, chains,
  independent unlocks/reset, pair ordering/consumption, bonuses, score overflow,
  and diagonal exclusion.
- Host save tests: defaults, sorted insertion/ties, settings/initials round trip,
  every protected byte corrupted individually, and missing commit marker.
- Actual ROM in PyBoy, both DMG and CGB: title and attract cards,
  credits, the supplied full-screen How to Play artwork with native Itty Bitty
  rules and a blank footer caption area (lettering, cleared area and surrounding art pixel-checked),
  entry/return through start and pause menus,
  held-button rejection, pause/new-game cancel,
  1-to-2-to-3 chain, four-six clear and five unlock, final placement/game-over,
  BCD initials, settings persistence, reboot, and corrupt-newest-slot recovery.
- The headless harness uses PyBoy's bundled boot program, not Nintendo ROMs.
  For DMG it sets the cartridge-entry CPU identifier to 1 because PyBoy's
  bundled boot reports CGB for a dual-compatible cartridge even with `cgb=False`.
  Game code itself is unchanged; the test restores the physical DMG contract.
- Native 160x144 screenshots are produced under `build/`; the test never
  overwrites an interactive emulator's battery save.
- Cartridge size/header/global checksum and bank usage are verified after build.

These checks are not a claim of exhaustive equivalence or hardware certification.
The Atari source was reviewed; no running Atari binary was available for a
side-by-side framebuffer or audio comparison. Physical DMG/GBC, flash-cartridge
power-loss behavior, extended play balance, and subjective music listening
remain release validation tasks. CI configuration is supplied; hosted Actions
execution is only verified after the changes are pushed.
