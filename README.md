# Shanghai C64 Demo

Standalone C64 demo for VICE built from the previous project base, now reworked into a pastel layout with a vertical hi-res PARALLAX logo on the left, a sprite-plasma capsule ribbon in the main field, SID music, and the preserved white lower-border scroller crawling across the bottom.

Music: "Over The Mountain Ascent", an original SID-style tune built from `src/music/over_mountain_sid.a`, bundled as `src/assets/sid.psid`, and relocated to `$1000` at assembly time.

Build:

```bash
./scripts/build.sh
```

This produces `build/shanghai.prg` and, when exomizer is installed (`brew install exomizer`), a self-extracting crunched `build/shanghai_sfx.prg` at roughly a third of the size. Ready-to-run copies of both are committed in `dist/`.

Run in VICE:

```bash
./scripts/run.sh
```

Regenerate the bundled vertical hi-res logo assets with:

```bash
python3 scripts/make_parallax_charmode.py
```

The border-scroller font (`src/assets/parallax_font8.bin`) can be rebuilt from a KickAssembler `.byte` charset dump with `python3 scripts/make_font8.py charset.txt`; the committed binary is a custom font whose source text is not bundled.

Regenerate the SID music asset with:

```bash
python3 scripts/make_over_mountain_sid.py
```
