# Hardware Ship Transition

The native Starwars scroller opens with one 48x42 TIE fighter moving from left
to right. The source-derived image is divided into four 24x21 quadrants. Each
quadrant overlays dark-detail and light-hull sprites, consuming all eight C64
hardware sprites. Black negative space separates the cockpit, wing braces, and
panel gaps. Forty small character-mode stars in white, gray, and light blue
provide the flyby's background without consuming additional sprites.

## Startup Order

1. Disable IRQ sources and select VIC bank 3.
2. Build and run the 90-frame hardware-sprite flyby.
3. Disable all sprites and hide the display.
4. Prepare the bitmap, starfield, logo, colors, and scroll buffers.
5. Start Galway playback and its raster IRQ.
6. Reveal the live bitmap from the center out.

The flyby is silent and finishes before music starts, keeping the existing
sound and plotter timing unchanged.

## Memory Layout

- Transition screen: `$c000`
- Transition sprite pointers: `$c3f8-$c3ff`
- Eight layered quadrant definitions: `$c400-$c5ff`
- Blank and star characters: `$c800-$c81f`
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

`scripts/generate_transition_sprites.py` crops the supplied TIE fighter,
reduces it into separate outlined detail and hull masks, divides both layers
into four quadrants, and writes `src/generated/transition_sprites.inc`. The
normal build regenerates this file before assembly.

`SHIP_TRANSITION_FRAMES` in `src/main.a` controls the flyby duration. The
current value is 90 PAL frames, or approximately 1.8 seconds.

## Motion

One 9-bit parent X coordinate drives all eight sprites. The right quadrants add
24 pixels to the parent X, the bottom quadrants add 21 pixels to the base Y,
and both layers in each quadrant share identical coordinates. This keeps all
seams locked while the composite crosses the VIC's 256-pixel X boundary.

The original Nobounds loader/direct paths are unchanged.
