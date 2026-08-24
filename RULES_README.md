# Dice Merge C64 Game Rules

These rules describe the Commodore 64 version of Dice Merge. The Apple II port has separate [Apple II Game Rules](apple2/RULES_README.md).

[Return to the main README](README.md)

## Piece Generation

Each turn normally produces one or two dice with values from 1 to 4. Once at least five value-5 dice are present on the board, each new piece has a 1-in-16 chance of containing one generated value-5 die.

A double piece can never contain two value-4 dice. Double pieces rotate in four directions and must fit entirely inside empty grid cells.

When no two edge-adjacent empty cells remain, the game switches permanently to single-die pieces. Filling the final empty cell ends the game.

## Placement

Valid targets show the dice normally. The current target uses a yellow marching-ants border, with two independently animated squares for a double die. Targets that overlap an occupied cell show the intended dice as gray dithered shadows and cannot be placed.

Placed dice pulse to acknowledge a successful move.

## Merging And Scoring

Three or more edge-connected equal dice merge at the placed die. Values progress from 1 through 6; a connected group of 6s disappears. New values can immediately trigger another merge.

Each merge scores the total face value of the consumed dice.

The first merge in every chain plays a happy rising C-E-G-C pulse arpeggio synchronized with the start of the merge animation. Cascading merges do not replay the first-merge cue.

## Merge Effects

Each merge fades the sidebar mascot through dark gray to black, then fades in one of the supplied hi-res comic bursts.

- Lower-value merges rotate through `AWESOME`, `BOOM`, `DANG`, `LETS GO`, `WHOA`, `WOW`, `YEAH`, and `YES`.
- Merging value-5 dice always shows `FIVES`.
- Merging value-6 dice always shows `SIXIES`.
- A value-1 merge keeps its word solid white.
- Value 2 begins entirely blue and changes to gray from left to right.
- Value 3 sends a green band from left to right across white.
- Value-4, value-5, and value-6 merges animate concentric red, orange, yellow, green, cyan, blue, and purple bands through the word.

The bursts are resized and centered across the full 80-pixel sidebar. Full squares along the destination row and column flash inward from all four grid edges while the dice pulse: white for the first merge and cyan for a chain merge.

Three sprite stars burst from the destination, jump outward, and fall in separate arcs into the next grid row. A second chain merge doubles the size of the firework stars. Creating a six follows the burst with three stars descending from the top to the bottom of the board. The upgraded die pauses for roughly half a second before a second chain merge collapses.

## New Game And Game Over

New Game spirals from the bottom-left cell toward the center. Game over reverses that effect, then wipes the full display from top to bottom with a solid gray band. Each band holds for 0.1 seconds before revealing a native multicolor Koala logo.

The completed Sixies image and large red `GAME OVER` banner remain visible for two seconds before the final score and five-entry high-score page replace the center panel. When a score takes first place, its complete high-score row flashes yellow and white until the player enters all three initials. A new first-place score persists until the PRG is reloaded.

The end-game display rotates through the title, high-score, and credits pages every ten seconds. A compact `PRESS N FOR NEW GAME` instruction remains at the bottom, and `N` starts a new game from any end-game page.

The logo uses one flat C64 color per letter, a continuous solid-white outer border, and a solid-black inner stroke with no dithering. New Game restores hi-res mode and resets the board, score, and single-die endgame mode without clearing the high-score table.
