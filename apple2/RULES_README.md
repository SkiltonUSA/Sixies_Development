# SIXIES Apple II Game Rules

SIXIES is a dice-merging puzzle played on a 5x5 grid. Place each supplied piece, combine equal dice, create chain reactions, and keep enough open space for future pieces.

[Return to the Apple II README](README.md)

## Objective

- Place every supplied single or paired piece on empty grid cells.
- Connect three or more dice with the same face value along their horizontal or vertical edges.
- Build higher-value dice and chain reactions to increase the score.
- Keep at least one valid placement available. Filling the final empty cell ends the game.

## Piece Generation

During normal play, paired pieces occur on two-thirds of turns and single dice occur on one-third.

Single dice follow these rules:

- Values 1, 2, and 3 may appear by themselves from the start.
- A standalone 4 becomes available when at least three value-4 dice exist on the board.
- A standalone 5 becomes available when at least four value-5 dice exist on the board.
- Value 5 never appears as part of a pair.

The allowed paired pieces are:

| Pair | Availability |
| --- | --- |
| `1+2` | Always |
| `1+3` | Always |
| `2+3` | Always |
| `2+4` | Always |
| `3+3` | Always |
| `3+4` | Always |

When the board has no adjacent empty cells for a pair, the game enters forced single-die mode. Two-thirds of forced singles are weighted toward eligible values beside empty cells; one-third use normal random selection. Normal pair generation resumes if clearing 5s or 6s creates adjacent empty space.

## Placement

- Move a piece to empty cells and rotate paired pieces through four orientations.
- Both dice in a pair must remain inside the grid and land on empty cells.
- A placement die flashes while waiting for input.
- A die positioned over an occupied cell is shown with diagonal hatching and cannot be placed.
- An invalid placement leaves the board unchanged and plays the descending bonk sound.

## Merging

- Three or more equal dice merge when connected by horizontal or vertical edges. Diagonal contact does not form a group.
- Values 1 through 5 merge into one die with the next value.
- Connected value-6 dice are removed instead of creating a value 7.
- A newly created die can immediately trigger another merge.
- Multiple merges resolve separately so every board change and score increase remains visible.
- Horizontal and vertical ripples accompany every merge.
- Merges consuming value-5 or value-6 dice add four simultaneous diagonal ripple arms.
- Merges of exactly three 5s or exactly three 6s also shake the grid horizontally.
- The merged location flashes and emits falling star sprites before the comic callout appears.
- `FIVES` is reserved for merging 4s into a 5, while `SIXIES` is reserved for merging 5s into a 6.
- `AWESOME` is reserved for the second and later generic merges produced by the same placement turn.

## Scoring

A merge awards the consumed face value multiplied by the number of dice in the connected group.

| Merge | Points |
| --- | ---: |
| Three 1s | 3 |
| Three 2s | 6 |
| Three 3s | 9 |
| Three 4s | 12 |
| Three 5s | 15 |
| Four 5s | 20 |

Larger connected groups score every consumed die. Removing 6s adds a 50-point bonus, so merging three 6s scores `3 x 6 + 50 = 68` points.

Each step in a chain reaction is scored separately and updates the five-digit total before the next merge begins.

## Controls

| Key | Game action |
| --- | --- |
| Arrow keys or `W`, `A`, `S`, `D` | Move the placement dice |
| `E` or `Q` | Rotate a paired piece |
| `Space` or `Return` | Place the current piece |
| `N` | Open the new-game confirmation prompt |
| `Y` / `N` | Confirm a new game / return to the current game |
| `I` | Show instructions |
| `Space` | Return from instructions to the unchanged game |
| `M` | Toggle all speaker sound effects |
| `A` through `Z` | Enter three initials after a qualifying game |

## High Scores

At game over, `Space`, `Return`, or `N` opens the high-score table. A qualifying score prompts for three initials, inserts the entry in descending order, and saves it to the disk's 56-byte `HISCORE` file. A score must exceed at least one existing entry to enter the ten-place table.

New disks contain these default entries:

| Rank | Name | Score |
| ---: | :---: | ---: |
| 1 | DOM | 1349 |
| 2 | PRI | 1020 |
| 3 | TWD | 893 |
| 4 | TAN | 802 |
| 5 | TB | 755 |
| 6 | ACE | 650 |
| 7 | MAX | 540 |
| 8 | ZED | 430 |
| 9 | BOT | 320 |
| 10 | CPU | 210 |

The two-letter `TB` name is stored with an invisible trailing space in the fixed three-character initials field.
