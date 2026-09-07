# Atari Sixies rules

The Atari merge, chain, scoring, forced-single, and RNG behavior follows the
Apple IIe core. Its dealt-piece probabilities and progression use the revised
Atari design described below.

## Implemented rules

- The board is 5x5 and groups connect only across horizontal or vertical edges.
- Normal generation is 75% pairs and 25% singles.
- The six opening ordered pairs are `1+2`, `1+3`, `2+3`, `3+1`, `3+2`, and
  `3+3`. The combinations `1+1`, `2+1`, and `2+2` never appear. `3+3` has a
  fixed 5% overall chance; the other opening pairs each have a 14% chance.
- Opening singles are 1, 2, and 3 with equal weighting, giving each an
  approximately 8.33% overall chance during normal play.
- Merging one connected group of four or more 4s permanently unlocks `3+4`
  and single `4` for the rest of that game. Fours can still be created by
  merging 3s before they are eligible to be dealt.
- Clearing one connected group of four or more 6s permanently unlocks `4+5`
  and single `5` for the rest of that game. Fives can still be created by
  merging 4s before they are eligible to be dealt.
- `3+3` remains fixed at 5% after each unlock. All other currently available
  pairs share the remaining 70%: about 11.67% each after the 4 milestone and
  exactly 10% each after the 6 milestone.
- Both deal milestones reset when a new game begins; removing their triggering
  dice later does not lock them again during the current game.
- Whenever at least four 4s are currently on the board, temporary four-pressure
  weighting takes priority over the ordinary unlocked pool. During a normal
  deal, `3+4` receives 35% and single `4` receives 15% (12.5% if single `5` is
  unlocked). Together, approximately half of deals contain a 4. `3+3` remains
  5%. Opening pairs containing 1 or 2 fall from 14% to 7% each, and single 1
  and 2 fall from about 8.33% to 2.5% each. This pressure ends when fewer than
  four 4s remain; permanent milestone unlocks are unaffected.
- If no adjacent empty cells remain, generation switches to matching singles;
  pair generation returns when adjacency returns.
- Crowded-board rescue begins before pairs become impossible. At 18-21 occupied
  cells, 50% of turns attempt a matching single; the other half use the normal
  75/25 deal. At 22-24 occupied cells, the matching attempt rises to 75%. If
  no adjacent pair fits, every deal attempts a matching single.
- Matching faces are weighted by empty neighboring squares. An empty square
  touching two equal eligible dice receives twice their weight, favoring moves
  that complete a merge. Faces 1-3 are always eligible; 4 uses either its
  milestone or active four-pressure condition, and 5 requires its milestone.
  Sixes are never dealt. If no eligible matching neighbor exists, generation
  falls back to the current normal single pool.
- Random rolls use the Apple IIe/cc65 four-byte generator. This avoids the
  conditional bias of the earlier one-byte Atari LFSR, which could omit `1+2`
  pairs after the preceding pair/single roll.
- A complete connected group of at least three equal dice merges at the placed
  origin. Values 1-5 advance by one; a group of 6s disappears.
- A pair resolves its origin first, then its second die if that cell still
  exists. New dice are resolved repeatedly at the same origin for chains.
- A merge's base award is `face value × connected count`. Creating a 5 adds
  25, creating a 6 adds 50, and removing a group of 6s adds 100. Chain position
  multiplies the complete base-plus-bonus award: the first merge from a
  placement is ×1, the second ×2, the third ×3, and so forth. Chain depth
  continues if the placed pair's second die reacts after the first.
- The score uses the Apple IIe's 16-bit unsigned arithmetic.
- `FIVES` identifies any merge consuming 4s, `SIXIES` identifies any merge
  consuming 5s, and `AWESOME` is reserved for later generic merges in a turn.
- Diagonal ripple arms accompany merges consuming 5s or 6s.
- The game ends when the generated piece has no valid empty placement.

## Presentation parity in this first port

The native build includes an inward row-and-column grid ripple with diagonal
arms for face-5 and face-6 merges, a grid-only shake for face-4 through face-6
events, a whole-screen flash when sixes disappear, a three-particle XOR star
firework, the multiplied `+points` award below the
permanent score, an outward-moving `2X`/`3X` chain badge, outcome-specific merge
callouts, a `CHAIN REACTION!` panel below the next-piece dice that remains for
one additional non-blocking second, merge tones, invalid-placement sound,
instructions, title music,
game-over presentation, and the persistent ten-entry high-score table with
three-initial entry. The playable generation, placement, merge, chain, scoring,
and high-face presentation effects are present.
