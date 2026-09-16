# Reference Screens and Artwork

This index separates visual references from build inputs and generated C64
data. Ports should work from source masters and use screenshots only to match
composition, spacing, and game feel.

## Stable screen references

- `docs/reference/gameplay-valid-target.png`: historical board, sidebar,
  score, preview, bottom controls, and a valid double target.
- `docs/reference/gameplay-invalid-target.png`: representative occupied target
  rendered with the two-cell shadow treatment.
- `src/assets/presents_preview.png`: generated Studio 313 presentation page.
- `src/assets/title_preview.png`: generated title page.
- `src/assets/title_prompt_sprites.bin`: generated five-sprite, versionless
  title prompt; the build combines it with the automatic intro `V1.xxx` sprite.
- `src/assets/game_over_koala_preview.png`: generated endgame logo.
- `src/assets/merge_callouts_preview.png`: generated merge-word atlas with
  72-by-64-pixel right-sidebar panels.
- `src/assets/main_mascot_preview.png`: generated 64 by 80 gameplay mascot.
- `src/assets/sidebar_logo_preview.png`: archived 80 by 32 gameplay-logo preview; no longer linked into the game.
- `src/assets/settings_dice_preview.png`: generated settings illustration.
- `src/assets/credits_logo_preview.png` and
  `src/assets/credits_mascot_preview.png`: generated credits art.
- `src/assets/gameplay_logo_preview.png`: compact gameplay wordmark generated
  for the space above the board.
- `src/assets/chain_reaction_preview.png`: generated 72-by-64 bitmap callout
  placed in the right-sidebar exclamation panel between merge links.
- `src/assets/font/SixiesFont_preview.png`, `SixiesFont16_preview.png`, and
  `SixiesDigits16_preview.png`: previews rendered from final font bytes.

The gameplay captures record intended layout, not exact current binary output;
the assembly implementation remains authoritative for behavior and generated
previews remain authoritative for current converted art.

## Source artwork

- `src/assets/Studio313.kla`: presentation-screen Koala master.
- `src/assets/title_logo_flat_master.png`: title composition master.
- `src/assets/game_over_logo_flat_master.png`: endgame composition master.
- `src/assets/main_mascot_master.png`: gameplay mascot master.
- `src/assets/sidebar_logo_master.png`: archived gameplay sidebar-logo master.
- `src/assets/settings_dice_master.png`: settings illustration master.
- `src/assets/credits_logo_master.jpg`: credits logo master.
- `src/assets/gameplay_logo_master.png`: green gameplay wordmark master.
- `src/assets/new_game_icon_master.png`: supplied overlapping-dice New Game
  badge used to generate the gameplay control sprite.
- `src/assets/credits_mascot_master.png`: credits mascot master.
- `src/assets/chain_reaction_master.png`: chain-reaction banner master.
- `src/assets/font/SixiesFont_sheet.png`: alphabet and digit source sheet.
- `src/assets/exclamations/*.png`: individual merge callout masters.
- `src/assets/die_one.asm` through `die_six.asm`: hand-authored C64 die assets.
- `src/assets/preview_dice_effects.asm`: runtime builder for inverse blinking
  previews and dithered invalid-placement previews.
- `src/assets/new_game.asm`: generated 24x21 New Game control sprite.
- `src/assets/settings.asm`: original hand-authored eight-tooth gear sprite.
- `src/assets/bottom_labels.asm`: compact labels placed beneath those sprites
  at the bottom of the gameplay side panels.
- `src/assets/bottom_icon_control.asm`: side-control icon raster multiplexing
  and focus-color control.

## Generated files

The Makefile regenerates converted bitmaps, screen/color data, Koala files,
packed streams, charsets, callout atlases, tables, and PNG previews. Do not edit
those outputs as if they were source art. Relevant converters include:

- `scripts/convert-title.py`
- `scripts/build-title-version.py`
- `scripts/convert-solid-koala.py`
- `scripts/convert-main-mascot.py`
- `scripts/build-gameplay-logo.py`
- `scripts/build-chain-reaction-sprite.py`
- `scripts/build-sidebar-logo.py`
- `scripts/pack-sidebar-logo.py`
- `scripts/convert-presents.py`
- `scripts/extract-font-sheet.py`
- `scripts/build-font-assets.py`
- `scripts/build-merge-callouts.py`
- `scripts/build-side-control-icons.py`
- `scripts/pack-koala.py`

Run `make` after changing a master or converter and inspect the corresponding
preview before accepting generated binary changes.
