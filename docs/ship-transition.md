# Hardware Ship Transition

The native Starwars scroller opens with a 48x42 TIE fighter moving left-to-right
and a 48x42 X-wing moving right-to-left along the bottom. Each source-derived
image is divided into four 24x21 quadrants, with detail and hull layers consuming
all eight C64 hardware sprites. A raster split reuses those sprites for the
X-wing after the TIE scanlines have finished. Black negative space preserves
the cockpit, wing braces, and panel gaps. The flyby uses the main scroller's
hires stars, repeating its upper pattern behind the lower X-wing.

## Startup Order

1. Disable IRQ sources and select VIC bank 3.
2. Prepare the shared bitmap starfield and screen colors.
3. Build and run the 90-frame hardware-sprite flyby over that bitmap.
4. Disable all sprites, then add the logo and scroll buffers while hidden.
5. Start Galway playback and its raster IRQ.
6. Reveal the live bitmap from the center out.

The flyby is silent and finishes before music starts, keeping the existing
sound and plotter timing unchanged.

## Memory Layout

- Transition screen: `$c000`
- Transition sprite pointers: `$c3f8-$c3ff`
- TIE layered quadrant definitions: `$c400-$c5ff`
- X-wing layered quadrant definitions: `$c600-$c7ff`
- Bitmap crawl screen: `$c000`
- Bitmap crawl data: `$e000`

All transition graphics share VIC bank 3 with the bitmap part, so no VIC bank
switch is needed during the handoff.

## Entry Points

`src/shiptransition.inc` exposes:

- `shiptransition_build_assets`
- `shiptransition_init`
- `shiptransition_update`
- `shiptransition_hide`

`scripts/generate_transition_sprites.py` crops the supplied TIE fighter and
X-wing, reduces each into separate outlined detail and hull masks, divides both
layers into four quadrants, and writes `src/generated/transition_sprites.inc`.
The normal build regenerates this file before assembly.

`SHIP_TRANSITION_FRAMES` in `src/main.a` controls the flyby duration. The
current value is 90 PAL frames, or approximately 1.8 seconds.

## Motion

Each ship has a 9-bit parent X coordinate. The right quadrants add 24 pixels to
that coordinate, the bottom quadrants add 21 pixels to the base Y, and both
layers share identical coordinates. This keeps all seams locked while the
composites cross the VIC's 256-pixel X boundary in opposite directions.

The original Nobounds loader/direct paths are unchanged.
