# Screen Fade Bobs Integration

This repo now contains a reusable character-mode `screenfadebobs` effect and a
single integration point in the native Star Wars scroller.

## Purpose

The effect was extracted from the Retro DNA transition browser so it can be
reused in other C64 parts without copying half of another demo. In this repo it
is used as a short visual pre-roll before the native hires-bitmap crawl starts.

## Files Changed

- `src/main.a`
- `src/screenfadebobs.inc`

## What The Native PRG Does Now

Only `build/StarwarsScrollerDemo.prg` and `build/StarwarsScrollerDemo-sfx.prg`
use the new effect.

Startup order in `src/main.a`:

1. Disable IRQ sources and select VIC bank 3.
2. Run `run_screenfadebobs_intro`.
3. Switch to hires bitmap mode.
4. Clear/fill the bitmap and screen RAM for the crawl.
5. Initialise Galway playback and the raster IRQ.
6. Enter the normal crawl loop.

The effect runs before `galway_init`, so the pre-roll is currently silent by
design. That was the safest integration because it does not disturb the
existing music IRQ timing or the bitmap setup path.

## Memory Layout

The integration keeps the effect in VIC bank 3 so the code does not have to
switch banks between the pre-roll and the bitmap crawl.

- Screen RAM for the effect: `$c000`
- Character set for the effect: `$c800`
- Bitmap crawl screen RAM: `$c000`
- Bitmap crawl bitmap: `$e000`
- Scroll data buffers: `$7800` CPU-only, outside the VIC bank

`$c800-$cfff` is safe for the effect charset in the current build because the
native crawl uses screen RAM at `$c000` and bitmap RAM at `$e000`, leaving that
charset slot free.

## Config Symbols In `src/main.a`

The integration maps the reusable include through these symbols:

- `screenfadebobs_screen_base = SCREEN`
- `screenfadebobs_color_base = $d800`
- `screenfadebobs_d018 = $02`
- `screenfadebobs_charset_base = SCREENFADEBOBS_CHARSET`
- `screenfadebobs_dst_ptr = $f9`
- `screenfadebobs_color_ptr = $fb`
- `screenfadebobs_border_color = $00`
- `screenfadebobs_background_color = $00`
- `screenfadebobs_multi1_color = $0c`
- `screenfadebobs_multi2_color = $01`
- `screenfadebobs_bob_color = $0f`

`SCREENFADEBOBS_FRAMES = 70` controls how long the intro stays on screen.

## Reusable Entry Points

The include exposes three entry points:

- `screenfadebobs_build_charset`
- `screenfadebobs_init`
- `screenfadebobs_update`

Expected call pattern:

1. Select the VIC bank you want to use.
2. Call `screenfadebobs_build_charset` once.
3. Call `screenfadebobs_init` once.
4. Call `screenfadebobs_update` once per frame.

## Why The Include Lives In `src/`

The goal is for another agent to be able to import the effect by reading one
file instead of mining transition-browser code. `src/screenfadebobs.inc`
contains:

- screen setup
- charset builder
- init/update loop
- draw routine
- screen/color fill helpers
- row lookup tables
- animation data
- private state

It does not depend on the transition browser anymore.

## What Was Not Changed

- `src/starwars_loader.a` is unchanged.
- `src/starwars_direct.a` is unchanged.
- The original Nobounds-loaded path is unchanged.
- The bitmap crawl renderer and music IRQ logic are unchanged after the intro
  returns.

## If Another Agent Wants Music During The Intro

Right now the intro is intentionally silent. To start music earlier, the safest
follow-up is:

1. Move `galway_init` before `run_screenfadebobs_intro`.
2. Install the raster IRQ before the intro loop.
3. Re-test the crawl startup timing and make sure the intro does not leave VIC
   registers in a state that breaks bitmap setup.

That is a separate change and was deliberately not folded into this integration.
