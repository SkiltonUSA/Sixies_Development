# Nobounds Plasma Menu

Standalone C64 demo built in this branch from routines and assets pulled from the Nobounds public source tree.

Included menu entries:

1. `Metalux Plasma` from `XMarksTheSpot/SourceCode/DemoParts/Metalux-Plasma.asm`
2. `Razorback Column Fade` derived from `NoBounds/Parts/PlasmaVector/PlasmaVectorIntro.asm`
3. `Razorback Bitmap View` using `NoBounds/Link/PlasmaVector/RazorbackUnbound.*`
4. `HiresLoader Columns` adapted from `NoBounds/Parts/HiresLoader/*`
5. `Razorback Plasma Background` using `NoBounds/Parts/PlasmaVector/Data/CombinedBitmap.map`
6. `StarWars Scroller` using the scroll text from `NoBounds/Parts/StarWars/StarWars.cpp`

Build:

```bash
./scripts/build.sh
```

Run in VICE:

```bash
./scripts/run.sh
```

Controls:

- `1` to `6` switch directly between menu entries
- `Space` returns to the menu

Entry 6 loads the original StarWars part files from disk (slow with true
drive emulation) and hands control over completely; like the standalone
`StarWars.d64`, the scroll loops forever and does not return to the menu.
