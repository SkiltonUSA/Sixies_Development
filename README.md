# Dice Merge for Commodore 64

A 5x5 hi-res puzzle game written in 6510 assembly for ACME. Place random single or double dice, merge connected matching values, and keep space available on the board.

The main grid screen includes a flat-color purple mascot in the left sidebar below the score. The upcoming single or double dice preview is positioned beneath the mascot so both remain visible.

The Sixies font is extracted from the supplied 1536x1024 reference sheet during the build. It generates `A-Z` and `0-9` as an 8x8 ASM table and 2048-byte charset. The `GAME OVER` banner uses those 8x8 glyphs, while the score uses separately extracted 16x16 numerals so the rounded counters and silhouettes retain more detail.

The game opens with a native C64 multicolor title screen using flat-color Sixies branding and solid outlines. While waiting, it alternates with the high-score table every five seconds. Press `Space`, `Return`, or joystick fire from either screen to enter the hi-res game board.

## Build and run

```sh
make
make run
```

The build creates `build/dice_merge.prg`. ACME is installed locally under `.tools/` when needed.

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
- `.`: development shortcut that randomly fills the board and triggers Game Over

Moving a die between grid cells plays the three-frame c64SIDkit `bounce` effect. Successful placement and double-die rotation play the higher-priority five-frame `portal_ping` effect through SID voice 1.

## Rules

Each turn normally produces one or two dice with values from 1 to 4. Once at least five value-5 dice are present on the board, each new piece has a 1-in-16 chance of containing one generated value-5 die. A double piece can never contain two value-4 dice. Double pieces rotate in four directions and must fit entirely inside empty grid cells.

Valid targets show the dice normally. The current target uses a yellow marching-ants border, with two independently animated squares for a double die. Targets that overlap an occupied cell show the intended dice as gray dithered shadows and cannot be placed.

Three or more edge-connected equal dice merge at the placed die. Values progress from 1 through 6; a connected group of 6s disappears. New values can immediately trigger another merge. Each merge scores the total value of the consumed dice.

When no two edge-adjacent empty cells remain, the game switches permanently to single-die pieces. Filling the final empty cell ends the game.

Placed dice pulse to acknowledge the move. On a merge, full squares along the destination row and column flash inward from all four grid edges while the dice pulse: white for the first merge and cyan for a chain merge. Three sprite stars burst from the destination, jump outward, and fall in separate arcs into the next grid row. A second chain merge doubles the size of the firework stars. Creating a six follows the burst with three stars descending from the top to the bottom of the board. The upgraded die pauses for roughly half a second before a second chain merge collapses. New Game spirals from the bottom-left cell toward the center. Game over reverses that effect, then wipes the full display from top to bottom with a solid gray band. Each band holds for 0.1 seconds before revealing a native multicolor Koala logo. The completed Sixies image and large red `GAME OVER` banner remain visible for two seconds before the final score and five-entry high-score page replace the center panel. A new first-place score prompts for three initials and persists until the PRG is reloaded. The end-game display then alternates between the title and high-score pages every ten seconds. A compact `PRESS N FOR NEW GAME` instruction remains at the bottom, and `N` starts a new game from either end-game page. The logo uses one flat C64 color per letter, a continuous solid-white outer border, and a solid-black inner stroke with no dithering. New Game restores hi-res mode and resets the board, score, and single-die endgame mode without clearing the high-score table.
