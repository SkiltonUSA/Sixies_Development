# Sixies Game Boy cardinal rule: locked playing-area dimensions

- Preserve the approved 5x5 board: exactly 100x100 screen pixels.
- Every grid square is exactly 20x20 pixels, including its borders.
- Board and preview dice use native 18x18 assets for all six faces. Never resize
  or resample the final source dice. scripts/rebuild-one-die.py uses the exact
  three-face silhouette and bevel with one centered 3x3 pip; its visible size
  must match that reference, not a smaller body padded into an 18x18 canvas.
  scripts/rebuild-two-die.py and
  scripts/rebuild-five-die.py share scripts/dice_frame.py to reuse the approved
  four-face outline and bevel at their exact native positions, including the
  restored top and bottom edges matching the three-face reference; never add an
  extra padding ring. Keep their solid 3x3 pips
  separated, including diagonally, and preserve their dark/light contrast.
- Center each 18x18 board canvas with a one-pixel inset on all four sides.
- Apply the per-face four-shade permutations in scripts/dice_shading.py during
  conversion, not to the original PNGs. Preserve pixel positions, transparency
  and pip shapes. Board and Next must use the same face shading; hover inversion
  follows shading. Keep the selected pip/body contrast at least two shade steps.
- Positioning requests may move the board or preview window, but must not change
  these dimensions. Only an explicit user request to change the dimensions can
  override this rule; do not resize the board to match a reference image.
- Keep background rendering, sprite effects, asset previews, and emulator
  regression checks aligned when moving the board.

Approved layout: board top-left (5, 22), preview artwork at (109, 70) with a
blank eight-pixel top padding and its window body starting at y=78. Do not
restore the legacy grid connector or tab above the preview. Coordinates are screen pixels
from the top-left, not Game Boy tilemap or OAM coordinates. The window is close
to the board's lower-right corner, rather than attached to the screen edge.
The preview window body is 48x48 pixels, with a 36x36 interior. Center a single
18x18 canvas in it; center pairs horizontally or vertically and preserve their
face order in all four rotations. Redraw the frame before the dice so rotation
and pair-to-single transitions leave no stale dice behind.
Keep the most recent normal preview cached so invalid feedback can end alongside
the sound without waiting for pixel composition. The preview owns tiles 15-46;
do not let its dynamic frame/dice overwrite the HUD, boundary or board canvas.
Only a rejected A-button placement with sound enabled triggers the falling-mascot
overlay inside the same 48x48 frame. Hovering or rotating over an invalid position
must keep the normal dice preview. The noise effect and overlay share a 19-VBlank
lifetime; restore native dice when it ends, even if the cursor remains invalid.
Keep this background overlay independent of chain sprites/callouts.
Free in-bounds hovering dice share a VBlank-driven 16-frame cycle: eight inverted,
eight normal. Only redraw their cells, never Next or the settled dice. Keep
invalid hatching steady; use the same hatch at the visible origin when a pair
extends off-grid, never an X across a die. A free partner still blinks when its other cell is
occupied. Disable hover flashing during the opening spiral,
blocking merge effects and other screens. Reduced flashing keeps a steady
inverted hover rather than blinking.

A one-pixel inspection boundary marks x=0/159 and y=0/143 on gameplay and
full-screen title/intro/game-over artwork. It does not change the board's
dimensions or position. Keep the gameplay boundary's tile phases aligned with
the screen scroll offsets; the score is inset far enough to avoid the boundary.
The gameplay boundary is pure black. Its dedicated CGB background palette must
not recolor the board, dice, or preview frame.

Gameplay's outer background uses a light dotted pattern in tile 255, with CGB
palette 3. Never pattern the board, Next window or score panel.
The score panel is 48x32 at screen (109,14), eight pixels above the grid,
horizontally aligned with Next and using its
beveled border artwork. Keep SCORE and all five digits centered inside the
frame. Merge awards appear above the merged die and travel to the score digits;
the displayed total updates on arrival. Use outlined popup OBJ tiles 32-34 and
sprites 0-2, never the chain badge's tiles/sprites. Reserve OBJ tiles 36-37 for
the merge particle and its blank 8x16-mode companion. Reduced flashing keeps the
award stationary. Preserve score arithmetic and buffered-input behavior.
The score panel's tilemap begins at
row 31 and wraps to rows 0-2; preserve the CGB palette across that wrap. Score tiles 224-247
must not be overwritten by callouts. Exclamation words occupy a temporary 64x32
transparent comic sprite overlay over the grid, opposite the merged dice and after
the flying award clears. They use the reserved OBJ tiles 0-31 and sprites 3-18, with CGB OBJ
palette 5. Preserve the grid through the transparent background; hide the callout
sprites afterward without altering the board tiles.
Every merge emits eight bright one-pixel particles from the merged die. Keep
their short trajectories separate from the larger chain
reaction firecracker burst.
Keep callouts suppressed during chain reactions. Score uploads are cached by value
and invalidated when preparing a different screen.

Chain firecracker stars use OBJ tiles 38-39, sprites 0-2, and CGB OBJ palettes
3-4. Keep the badge in sprites 3-18; it uses OBJ tiles 0-15 and shares the
reserved OBJ pool with callouts and
must never overwrite gameplay background tiles 55-255. Run the three star bursts on a
60-VBlank clock without blocking gameplay; clear them on screen changes and
before another merge reuses sprites 0-2. Clear the complete prior badge before
any new merge reuses sprites 3-7. Reduced flashing disables the bursts.
