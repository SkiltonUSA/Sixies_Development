#!/usr/bin/env python3
"""Convert the supplied STAR / RETRODNA / WAR artwork to C64 hires."""

from pathlib import Path

from generate_logo import BAYER_4X4, decode_png, display_tone, sample_area
from generate_vader2 import PALETTE, color_error, write_rgb_png


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "assets" / "star_retro_war_vector_render.png"
PREVIEW_OUT = ROOT / "src" / "assets" / "star_retro_war_prelude_c64.png"
BITMAP_OUT = ROOT / "src" / "generated" / "prelude_hires_bitmap.bin"
BITMAP_PRG_OUT = ROOT / "src" / "generated" / "prelude_hires_bitmap.prg"
COLOR_OUT = ROOT / "src" / "generated" / "prelude_hires_colors.bin"
COLOR_PRG_OUT = ROOT / "src" / "generated" / "prelude_hires_colors.prg"

WIDTH = 320
HEIGHT = 200
INKS = (1, 6, 7, 8, 12, 14, 15)
VECTOR_CROP = (55, 55, 786, 551)


def main() -> None:
    source_width, source_height, source_rows = decode_png(SOURCE)
    left, top, right, bottom = VECTOR_CROP
    crop_width = right - left
    crop_height = bottom - top
    scale = min(WIDTH / crop_width, HEIGHT / crop_height)
    content_width = round(crop_width * scale)
    content_height = round(crop_height * scale)
    offset_x = (WIDTH - content_width) // 2
    offset_y = (HEIGHT - content_height) // 2

    pixels = [[PALETTE[0]] * WIDTH for _ in range(HEIGHT)]
    for y in range(content_height):
        sy0 = top + y * crop_height / content_height
        sy1 = top + (y + 1) * crop_height / content_height
        for x in range(content_width):
            sx0 = left + x * crop_width / content_width
            sx1 = left + (x + 1) * crop_width / content_width
            r, g, b, _ = sample_area(source_rows, sx0, sy0, sx1, sy1)
            pixels[offset_y + y][offset_x + x] = (r, g, b)

    bitmap = bytearray(8000)
    colors = bytearray(1000)
    rendered = [[PALETTE[0]] * WIDTH for _ in range(HEIGHT)]
    for cell_y in range(25):
        for cell_x in range(40):
            visible = []
            mask = []
            for y in range(8):
                for x in range(8):
                    px = cell_x * 8 + x
                    py = cell_y * 8 + y
                    pixel = pixels[py][px]
                    yellow_path = (
                        pixel[0] > 35
                        and pixel[1] > 30
                        and pixel[0] > pixel[2] * 1.6
                        and pixel[1] > pixel[2] * 1.5
                    )
                    threshold = 26 if yellow_path else (
                        52 + (BAYER_4X4[py & 3][px & 3] + 0.5) * 11
                    )
                    active = display_tone(pixel) > threshold
                    mask.append(active)
                    if active:
                        visible.append(pixel)

            if any(
                r > 35 and g > 30 and r > b * 1.6 and g > b * 1.5
                for r, g, b in visible
            ):
                ink = 7
            elif visible:
                average = tuple(
                    sum(pixel[channel] for pixel in visible) // len(visible)
                    for channel in range(3)
                )
                ink = min(INKS,
                          key=lambda color: color_error(average, PALETTE[color]))
            else:
                ink = 1
            colors[cell_y * 40 + cell_x] = ink

            for y in range(8):
                value = 0
                py = cell_y * 8 + y
                for x in range(8):
                    px = cell_x * 8 + x
                    active = mask[y * 8 + x]
                    if active:
                        value |= 0x80 >> x
                    rendered[py][px] = PALETTE[ink] if active else PALETTE[0]
                bitmap[cell_y * 320 + cell_x * 8 + y] = value

    PREVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    BITMAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_rgb_png(PREVIEW_OUT, rendered)
    BITMAP_OUT.write_bytes(bitmap)
    BITMAP_PRG_OUT.write_bytes(bytes((0x00, 0xe0)) + bitmap)
    COLOR_OUT.write_bytes(colors)
    COLOR_PRG_OUT.write_bytes(bytes((0x00, 0xd8)) + colors)
    print(
        f"Wrote {PREVIEW_OUT.relative_to(ROOT)} ({source_width}x{source_height}, "
        f"crop={crop_width}x{crop_height}@{left},{top}, "
        f"fit={content_width}x{content_height}@{offset_x},{offset_y}), "
        f"{len(bitmap)} bitmap bytes and {len(colors)} color bytes"
    )


if __name__ == "__main__":
    main()
