# Atari Sixies rules

The Atari rules core intentionally follows `apple2/RULES_README.md`, not the
older C64 generation variant.

## Implemented rules

- The board is 5x5 and groups connect only across horizontal or vertical edges.
- Normal generation is two-thirds pairs and one-third singles.
- The six pair choices are `1+2`, `1+3`, `2+3`, `2+4`, `3+3`, and `3+4`.
- Singles 1-3 begin unlocked. A single 4 unlocks with three board 4s; a single
  5 unlocks with four board 5s. Value 5 never occurs in a pair.
- If no adjacent empty cells remain, generation switches to singles. Two-thirds
  of those singles are weighted by eligible faces next to empty cells. Pair
  generation returns when adjacency returns.
- A complete connected group of at least three equal dice merges at the placed
  origin. Values 1-5 advance by one; a group of 6s disappears.
- A pair resolves its origin first, then its second die if that cell still
  exists. New dice are resolved repeatedly at the same origin for chains.
- Every merge scores `face value * connected count`. Removing 6s adds 50.
- The score saturates at 65,535 and the game ends when no empty cell remains.

## Presentation parity in this first port

The native build includes a centered XOR merge-star flash, merge callouts,
merge tones, invalid-placement sound, instructions, title music, and game-over
presentation. It does not yet include
the Apple II's persistent ten-entry high-score file and initials editor, nor the
full C64/Apple ripple, shake, three-particle falling fireworks, credits, and
attract-mode animation sequence. Those are presentation/persistence additions; the playable
generation, placement, merge, chain, and scoring core above is present.
