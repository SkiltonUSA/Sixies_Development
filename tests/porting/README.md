# Gameplay Conformance Vectors

`gameplay-vectors.json` is the portable behavioral contract for Sixies. Boards
are five arrays of five row-major cells. Operations exercise legal placement,
active-cell resolution, complete piece placement, deterministic spawning, and
available-space detection. C64 input sequences additionally lock down the
`Q`/`E` keyboard rotation mapping, fire-release placement, held-fire joystick
rotation chords, and the `Y`-to-confirm/`N`-to-cancel New Game prompt.

Run the dependency-free Python oracle with:

```sh
make test-porting
```

A platform port should consume the same JSON from its host-side test runner.
Do not call the Python implementation from shipping game code, and do not copy
expected results out of the vectors into special cases. Implement the rules,
then compare complete board state, chain-multiplied score, ordered merge events,
RNG state, piece state, dynamic single-required state, and game-over state. A
placement's ordered merge events use multipliers 1, 2, 5, 10, 20, and 40,
capped at 40, including events from the second cell of a double.

When adding a rule or fixing an ambiguity, first add a vector that fails for
the old behavior. Update `docs/game-rules.md` and the C64 implementation in the
same change.
