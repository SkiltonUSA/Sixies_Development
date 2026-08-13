# Dice Merge for Commodore 64

A 5x5 hi-res puzzle game written in 6510 assembly for ACME. Place random single or double dice, merge connected matching values, and keep space available on the board.

The main grid screen includes a flat-color purple mascot in the left sidebar below the score. The upcoming single or double dice preview is positioned beneath the mascot so both remain visible.

The Sixies font is reproduced from the supplied 1536x1024 reference sheet during the build, at two sizes. Every glyph on the sheet is a flat colored body inside a white outline, so only the body is sampled; the outline is discarded because it anti-aliases through the same gray that fills `D`, `J`, `P`, `V`, `2` and `8`, and would otherwise fatten every letter by a pixel. Each alphabet row contributes its own cap line and baseline, so the whole set shares one vertical rhythm.

`SixiesFont16.bin` is the faithful cut: 36 glyphs at 16x16, each a 2x2 block of characters, keeping the rounded bowls, the heavy stems and the tiny counters. Area coverage alone closes the counters of `A`, `B`, `D`, `P`, `R`, `4`, `6`, `8` and `9`, so every enclosed region in the source is reopened after thresholding. `Q` keeps its tail; the round glyphs that clear the baseline by a single source pixel are trimmed back so they do not eat the line gap. The credits cards and the score digits use this cut.

`SixiesFont_charset.bin` is the body-text cut: the same alphabet at 8x8 in a 2048-byte ASCII-indexed charset, used by the `GAME OVER` banner and the high-score page. Seven rows of cap height cannot hold the blobby `M` and `W` middles, the curled `C` and `G` terminals or the `K` arms without collapsing them into slabs that read as the wrong letter, so fifteen glyphs are hand drawn in `OVERRIDES_8X8`; the rest are resampled. `make` regenerates both cuts, their previews, and the derived banner and score tables.

The game opens with a native C64 multicolor title screen using flat-color Sixies branding and solid outlines. While waiting, it rotates through the title, high-score, and credits pages every five seconds. The credits keep a light-green Sixies logo and dice mascot fixed while Designed By, Graphic Arts, Music, and 2026 cards fade in and out in sequence. Press `Space`, `Return`, or joystick fire from any attract screen to enter the hi-res game board.

## Build and run

```sh
make
make run
```

The build creates `build/dice_merge.prg`. ACME is installed locally under `.tools/` when needed.

The startup title and high-score attract screens play `Eternity #1 (intro)` by Przemyslaw Lewandowski (Sonix), 1995 Undying/Sun Designs. A dedicated raster IRQ keeps playback continuous while title and high-score graphics are copied. The music returns when game over begins and continues through the end title/high-score rotation. Its SID player is relocated to RAM at `$A000`, called at 50 Hz on both PAL and NTSC machines, and stopped before gameplay begins.

## Sound design

c64SIDkit is installed locally under `.tools/c64SIDkit` for SID sound-effect authoring. Restore the installation or open its graphical tweaker with:

```sh
make setup-sidkit
make sidkit
```

The command-line exporter is available at `.tools/c64SIDkit/.venv/bin/sid-sfx`.

## Controls

- `W`, `A`, `S`, `D` or joystick port 2: move the current piece
- `R` or `Q`: rotate a double piece
- `Space`, `Return`, or joystick fire: place the piece
- `N`: clear the board and start a new game
- `Tab`: open or close the Settings instructions
- `N` while Settings is open: show the next instructions page
- From the grid's bottom row, press joystick down to focus the Settings gear, then fire to open it; press up to return to the grid
- `.`: development shortcut that randomly fills the board and triggers Game Over

Moving a die between grid cells plays the three-frame c64SIDkit `bounce` effect. Successful placement and double-die rotation play the higher-priority five-frame `portal_ping` effect through SID voice 1. The new-game grid ripple uses a randomized sawtooth effect reconstructed from the Sound FX Kit `TEST11` controls and stops when the setup animation finishes. Trying to place a die outside the board or over an occupied cell plays a custom low triangle "bonk" with a rapid downward pitch sweep.

## Rules

Each turn normally produces one or two dice with values from 1 to 4. Once at least five value-5 dice are present on the board, each new piece has a 1-in-16 chance of containing one generated value-5 die. A double piece can never contain two value-4 dice. Double pieces rotate in four directions and must fit entirely inside empty grid cells.

Valid targets show the dice normally. The current target uses a yellow marching-ants border, with two independently animated squares for a double die. Targets that overlap an occupied cell show the intended dice as gray dithered shadows and cannot be placed.

Three or more edge-connected equal dice merge at the placed die. Values progress from 1 through 6; a connected group of 6s disappears. New values can immediately trigger another merge. Each merge scores the total value of the consumed dice.

The first merge in every chain plays a happy rising C-E-G-C pulse arpeggio synchronized with the start of the merge animation. Cascading merges do not replay the first-merge cue.

When a score takes first place, its complete high-score row flashes yellow and white until the player enters all three initials.

When no two edge-adjacent empty cells remain, the game switches permanently to single-die pieces. Filling the final empty cell ends the game.

Placed dice pulse to acknowledge the move. Every merge also shouts one of eleven exclamations — `WOW!`, `YES!`, `YAY!`, `BOOM!`, `DANG!`, `WHOA!`, `YEAH!`, `FIVES!`, `SIXIES!`, `AWESOME!` or `LETS GO!` — picked at random and set across the sidebar mascot for the length of the merge animation, then cleared by redrawing him. The phrases are set in the Sixies charset at double height, eight characters wide to match the mascot panel, and take the merge tint, so a chain merge shouts in cyan. On a merge, full squares along the destination row and column flash inward from all four grid edges while the dice pulse: white for the first merge and cyan for a chain merge. Three sprite stars burst from the destination, jump outward, and fall in separate arcs into the next grid row. A second chain merge doubles the size of the firework stars. Creating a six follows the burst with three stars descending from the top to the bottom of the board. The upgraded die pauses for roughly half a second before a second chain merge collapses. New Game spirals from the bottom-left cell toward the center. Game over reverses that effect, then wipes the full display from top to bottom with a solid gray band. Each band holds for 0.1 seconds before revealing a native multicolor Koala logo. The completed Sixies image and large red `GAME OVER` banner remain visible for two seconds before the final score and five-entry high-score page replace the center panel. A new first-place score prompts for three initials and persists until the PRG is reloaded. The end-game display then rotates through the title, high-score, and credits pages every ten seconds. A compact `PRESS N FOR NEW GAME` instruction remains at the bottom, and `N` starts a new game from any end-game page. The logo uses one flat C64 color per letter, a continuous solid-white outer border, and a solid-black inner stroke with no dithering. New Game restores hi-res mode and resets the board, score, and single-die endgame mode without clearing the high-score table.
