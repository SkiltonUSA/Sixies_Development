# Sixies Game Rules

This document specifies gameplay behavior independently of C64 graphics and
sound. It describes the current implementation in `src/grid_base.asm` and is
the contract for ports.

## State model

The board is a 5 by 5 grid. Coordinates start at `(0,0)` in the top-left and
are stored row-major as `index = y * 5 + x`. Each cell contains:

- `0`: empty
- `1` through `6`: a die of that value

The score is an unsigned decimal value from 0 through 9999. It saturates at
9999 instead of wrapping. `singlesOnlyMode` is a transient implementation flag
recomputed from the current board before every draw; it never latches across
turns.

A current piece has one or two values, an origin coordinate, and an orientation.
Orientations are `0 = right`, `1 = down`, `2 = left`, and `3 = up`. For a
single, orientation has no gameplay effect.

## New game

New Game clears all 25 cells, resets score to zero, clears game over and the
transient single-required flag, seeds the random generator from machine timing with a
non-zero odd byte, and generates the first piece. The in-memory high-score
table is retained until the program is reloaded.

During active gameplay, pressing `N` or activating the focused New Game side
control first displays `Y OR N TO CONFIRM`. `Y` confirms and performs New
Game; `N` cancels and preserves the current board, piece, and score. Starting
after game over or from an attract page remains immediate because no playable
game is being discarded.

## Piece generation

The generator uses an 8-bit state. One random byte advances the state as:

```text
next = (state << 1) & 255
if state bit 7 was set: next = next XOR 0x1d
state = next
```

The state is never intentionally seeded with zero. Each piece is selected from
this fixed weighted table; doubles are ordered because die 0 is the rotation
origin:

| Deal | Weight |
| --- | ---: |
| `1` | 5 |
| `2` | 3 |
| `3` | 1 |
| `1+2` | 5 |
| `1+3` | 8 |
| `2+1` | 10 |
| `2+3` | 1 |
| `3+1` | 4 |
| `3+2` | 2 |

The total weight is 39. Selection advances the RNG until its byte is in the
inclusive range 1 through 234; bytes 235 through 255 are rejected. The deal
index is `(byte - 1) modulo 39`. Because 234 is exactly six times 39, every
table slot has six accepted RNG bytes and the weights are exact over the
accepted state cycle.

Single deals have total weight 9/39 and doubles have total weight 30/39.
Values 4, 5, and 6 have no base-table weight. Deals `1+1`, `2+2`, `3+3`, and
all deals containing 4 through 6 have zero base weight.

Before each selection, the generator checks the current board for an
orthogonally adjacent pair of empty cells. If none exists, only the three
single entries are eligible: `1` with weight 5, `2` with weight 3, and `3`
with weight 1. A selected double is rejected and selection repeats, preserving
the single weights instead of converting die 0 from a double. This condition
is not permanent. If a single causes a merge that reopens adjacent blank
cells, the next draw immediately uses the complete 39-weight table again.

If at least one blank and one value-5 die are currently on the board, every
visible generated value 2 is eligible for promotion. An exact 5% roll replaces
that 2 with a 4. The roll accepts RNG bytes 1 through 240, rejects 241 through
255, and succeeds on residue 6 of `(byte - 1) modulo 20`. The fixed base table
never contains two value-2 dice in one deal, so at most one promotion roll is
made per piece. A full board and pieces without a visible 2 consume no
promotion RNG byte. Removing the last value-5 die disables the rule.

While the current board requires a single, every occupied cell orthogonally
adjacent to at least one blank cell is a neighbor-match candidate. Each candidate cell is
included once even if it touches more than one blank. If at least one candidate
exists, the generator makes an exact 10% bonus roll. On success it uniformly
selects one candidate cell and replaces the generated single with that cell's
value. This can copy values 4, 5, or 6 through the endgame bonus. A full board
has no candidates and consumes no bonus RNG byte. Rejection sampling makes both
the 10% roll and candidate selection unbiased. Promotion runs before this
neighbor bonus, so a successful neighbor match can replace a promoted 4.

The new cursor starts at `(2,2)` facing right.

The timing-derived odd seed set gives the first piece of a new game a distinct
deterministic state-space distribution. Successive pieces are also correlated;
they are not independent table rolls. The exact weighted, opening, RNG-state,
and dynamic single-required distributions are generated in
`docs/piece-probabilities.md`.

## Movement and placement

The cursor is clamped to the 5 by 5 board; it does not wrap. `Q` rotates a
double counterclockwise and `E` rotates it clockwise through right, down, left,
and up. On joystick port 2,
holding fire and pressing left rotates counterclockwise while fire+right rotates
clockwise. Returning the stick to center while retaining fire rearms another
rotation; releasing fire after a rotation does not place. Fire without a
rotation places when released. A single ignores rotation chords.

A placement is valid only when the origin is in bounds and empty and, for a
double, the oriented second cell is also in bounds and empty. Dice may touch
existing dice; touching does not make placement invalid. Only overlap or an
out-of-bounds second cell is invalid.

Both cells of a valid double are written before any merge is resolved. The
origin cell is then resolved completely, including all of its chain reactions.
For a double, the original second index is resolved afterward only if that cell
is still non-empty. This origin-first ordering must be preserved because a
merge from the first die can clear, upgrade, or connect to the second die.

## Groups and merging

A group is the complete orthogonally connected component of cells with the
same value as the active cell. Left, right, up, and down count; diagonals do
not. A group containing fewer than three cells does nothing.

A chain multiplier starts at 1 for each placed piece. Successive merge events
use multipliers 1, 2, 5, 10, 20, and 40. Merge events after the sixth remain at
40. For doubles, the chain position carries from the origin's complete
resolution into resolution of the second cell.

A group containing three or more cells merges as follows:

1. Award `3 * current die value * chain multiplier` points. The scoring base
   remains three dice even when the connected component contains four or more.
   If the consumed value is 6, add a separate 150-point elimination bonus.
   Then advance to the next chain multiplier for a possible subsequent merge.
2. Clear every cell in the connected component.
3. If the consumed value is 1 through 5, place one die with value plus one at
   the active index. A group of four or more still makes exactly one die.
4. If the consumed value is 6, leave all cells empty and stop resolving this
   active index.
5. Otherwise, find the connected component at the same active index again. If
   it now has at least three cells, repeat the merge. This is a chain reaction.

Examples:

- Three connected 1s become one 2 and score 3.
- Four connected 2s become one 3 and score 6 because every merge uses the
  fixed three-die scoring base.
- Three 1s that create a 2 adjacent to two existing 2s immediately become one
  3 and score 15 total: 3 for the first group and 12 for the second
  (`3 cells * value 2 * multiplier 2`).
- Four successive merges of values 1, 2, 3, and 4 score 180 total:
  `3 + 12 + 45 + 120`.
- Three or more connected 6s disappear. As a first merge they score 168:
  `3 * 6 * 1` normal points plus the 150-point elimination bonus.

Animation delays, colors, callout words, shaking, fireworks, and sounds do not
alter board or score results. Ports may change their timing while preserving
the ordered merge events.

## Endgame and high scores

Before every new piece is presented, the game checks for an adjacent pair of
empty cells. If none exists for that draw, it selects only from the three
single entries. The offered piece is then searched against every board
coordinate; doubles are searched in all four orientations. If no legal
placement exists, game over begins. A later merge can reopen double space, so
the fallback never becomes permanent. Normal play reaches game over when all
25 cells are occupied.

The development `.` shortcut fills every cell with random values 1 through 6
and then runs the same spawn/game-over path.

At game over, the score qualifies for the five-entry table only when it is
strictly greater than an existing entry. Equal scores do not displace the
earlier entry. A qualifying score is inserted in descending order and starts
as `AAA`; the player enters three letters. High scores are RAM-only and reset
when the PRG is reloaded.

## Conformance

Canonical examples live in `tests/porting/gameplay-vectors.json`. Run:

```sh
make test-porting
```

The validator covers placement boundaries, orthogonal connectivity, groups
larger than three, six removal, chain reactions, origin-first double behavior,
generation constraints, score saturation, adjacent-space detection, and full
board game over.
