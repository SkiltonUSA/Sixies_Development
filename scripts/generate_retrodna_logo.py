#!/usr/bin/env python3
"""Convert the RetroDNA artwork into a dithered 320x80 hires banner."""

from pathlib import Path

from generate_logo import (BAYER_4X4, content_bbox, decode_png, display_tone,
                           luminance, nearest_c64, sample_area)

ROOT = Path(__file__).resolve().parent.parent
PNG_PATH = ROOT / "src" / "assets" / "retrodna_logo.png"
PART1_PATH = ROOT / "src" / "generated" / "retrodna_logo_part1.bin"
PART2_PATH = ROOT / "src" / "generated" / "retrodna_logo_part2.bin"
COLORS_PATH = ROOT / "src" / "generated" / "retrodna_logo_colors.bin"

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 80
CONTENT_LEFT = 16
CONTENT_TOP = 8
CONTENT_WIDTH = 288
CONTENT_HEIGHT = 64
LIGHT_BLUE_SHADOW_THRESHOLD = 28


def retrodna_color(rgb) -> int:
    color = nearest_c64(rgb)
    if color == 6 and luminance(rgb) >= LIGHT_BLUE_SHADOW_THRESHOLD:
        return 14
    return color


def main() -> None:
    width, height, rows = decode_png(PNG_PATH)
    left, top, right, bottom = content_bbox(width, height, rows)
    crop_width = right - left
    crop_height = bottom - top
    ink = [[False] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
    cell_rgb = [[[] for _ in range(40)] for _ in range(10)]

    for y in range(CONTENT_TOP, CONTENT_TOP + CONTENT_HEIGHT):
        source_y = y - CONTENT_TOP
        sy0 = top + source_y * crop_height / CONTENT_HEIGHT
        sy1 = top + (source_y + 1) * crop_height / CONTENT_HEIGHT
        for x in range(CONTENT_LEFT, CONTENT_LEFT + CONTENT_WIDTH):
            source_x = x - CONTENT_LEFT
            sx0 = left + source_x * crop_width / CONTENT_WIDTH
            sx1 = left + (source_x + 1) * crop_width / CONTENT_WIDTH
            r, g, b, a = sample_area(rows, sx0, sy0, sx1, sy1)
            threshold = (BAYER_4X4[y & 3][x & 3] + 0.5) * 16
            ink[y][x] = a > 128 and display_tone((r, g, b)) > threshold
            if ink[y][x]:
                cell_rgb[y // 8][x // 8].append((r, g, b))

    bitmap = bytearray()
    for row in range(10):
        for col in range(40):
            for line in range(8):
                value = 0xff
                for bit in range(8):
                    if ink[row * 8 + line][col * 8 + bit]:
                        value &= ~(0x80 >> bit)
                bitmap.append(value)

    if any(value != 0xff for value in bitmap[:320] + bitmap[-320:]):
        raise SystemExit("RetroDNA artwork escaped its eight-row storage area")

    # Rows 1-6 fit in the unused $8800-$8fff gap. Rows 7-8 live at $c800.
    PART1_PATH.write_bytes(bitmap[320:7 * 320])
    PART2_PATH.write_bytes(bitmap[7 * 320:9 * 320])
    colors = bytearray()
    for row in cell_rgb:
        for samples in row:
            if not samples:
                colors.append(1)
                continue
            average = tuple(sum(sample[channel] for sample in samples)
                            // len(samples) for channel in range(3))
            colors.append(retrodna_color(average))
    COLORS_PATH.write_bytes(colors)
    print(f"Wrote textured RetroDNA banner from {width}x{height} source "
          f"({len(PART1_PATH.read_bytes()) + len(PART2_PATH.read_bytes())} "
          f"bitmap bytes, {len(colors)} color bytes, "
          f"{len(set(colors))} ink colors)")


if __name__ == "__main__":
    main()
