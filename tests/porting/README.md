# Gameplay Conformance Vectors

`gameplay-vectors.json` is the portable behavioral contract for Sixies. Boards
are five arrays of five row-major cells. Operations exercise legal placement,
active-cell resolution, complete piece placement, deterministic spawning, and
available-space detection.

Run the dependency-free Python oracle with:

```sh
make test-porting
```

A platform port should consume the same JSON from its host-side test runner.
Do not call the Python implementation from shipping game code, and do not copy
expected results out of the vectors into special cases. Implement the rules,
then compare complete board state, score, ordered merge events, RNG state,
piece state, single-only state, and game-over state.

When adding a rule or fixing an ambiguity, first add a vector that fails for
the old behavior. Update `docs/game-rules.md` and the C64 implementation in the
same change.
