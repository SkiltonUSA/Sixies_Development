# Apple generated-asset contracts

The supplied Apple II generated headers and includes reproduce byte-for-byte
from the repository's generators. They describe Apple DHGR bank layouts, not
portable bitmap files, so the Atari port consumes their source masters and
translates their intent into ANTIC-F assets.

| Apple interface | Atari mapping |
| --- | --- |
| `dice_assets.h` | Six 24-row faces are rebuilt from the supplied ACME dice into `dice.bin`; Apple main/aux masks are intentionally omitted. |
| `footer_prompt.inc` | The prompt is rendered with the Atari bitmap font and supports Fire, Space, and Start. |
| `game_over_assets.h` | `game_over_master.png` becomes the native 240x120 illustrated Game Over panel. |
| `high_score_assets.h` | Geometry and font metadata are retained as the reference for the planned persistent high-score stage; no Apple RLE is linked into the 64K runtime. |
| `instructions_assets.h` / `INSTRUCT.RLE` | The supplied boxed design and complete rules are rebuilt as a 320x192 Atari screen, with Atari hardware labels and WASD/joystick controls, then packed into `instructions.rle`. |
| `merge_effects.h` | All ten official merge-word masters feed the Atari callout atlas in the supplied order. The matching Apple preview PNGs are the visual contract; the supplied `merge_star.png` maps to a centered XOR flash generated from the shared four-point sprite. |
| `presents_assets.h` | `presents_master.ppm` becomes a centered native startup screen in `presents.rle`. |
| `score_digits.inc` | Atari score digits use the shared bitmap font; Apple DHGR byte masks and scanline addresses are omitted. |

The generated Apple checksums remain useful for verifying the Apple build, but
Atari assets have different packing and therefore different byte counts and
checksums.

The Atari full-screen streams use a compact PackBits-style format: bit 7 marks
a repeated byte, while the lower seven bits encode a 1-128 byte packet length.
They decode directly across the physical `$8000-$9EFF` framebuffer, including
the 96-byte ANTIC boundary gap, without allocating a second 64K buffer.

## Verified Apple release baseline

The supplied `sixies.po` is the complete 140K ProDOS 2.4.3 release volume
`/SIXIES/`. It contains the crunched `SIXIES` executable, all four presentation
screens, grid and dice data, `MERGESTAR`, ten `FX00`-`FX09` words, and the
persistent high-score data/font. Every asset extracted from that disk matches
the output of this checkout's Apple generators byte-for-byte.

A clean `make -C apple2 disk` also reproduces the exact 11,954-byte executable
payload (SHA-256 `63cdaa2ce4fe7d6281e3276f3f5320e3384d337713bc38b36ee4f631de3d7e38`).
The supplied link map has the same segment geometry and exports as the rebuild;
its textual differences are build-workspace paths. Important parity anchors
include `_run_merge_grid_shake`, `_save_merge_effect_background`,
`_restore_merge_effect_background`, and `_xor_merge_star` in the Apple II
language-card segment at `$D400-$DFFE`.

This establishes the checked-in Apple source—not the platform-specific `.po`
or link addresses—as the canonical behavior source for the Atari port. The
Atari build translates those rules and effects into ANTIC, POKEY, and Atari
disk formats rather than embedding ProDOS or Apple DHGR binaries.
