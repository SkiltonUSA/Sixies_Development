#!/usr/bin/env python3
"""Convert the supplied Star Wars title into a temporary 320x96 hires image."""

from pathlib import Path

from generate_logo import content_bbox, decode_png, display_tone, sample_area

ROOT = Path(__file__).resolve().parent.parent
PNG_PATH = ROOT / "src" / "assets" / "starwars_intro_logo.png"
OUT_PATH = ROOT / "src" / "generated" / "starwars_intro_logo.bin"
PRG_OUT_PATH = ROOT / "src" / "generated" / "starwars_intro_logo.prg"

SCREEN_WIDTH = 320
SCREEN_HEIGHT = 96
CONTENT_LEFT = 24
CONTENT_TOP = 4
CONTENT_WIDTH = 272
CONTENT_HEIGHT = 88
BAYER_8X8 = (
    (0, 48, 12, 60, 3, 51, 15, 63),
    (32, 16, 44, 28, 35, 19, 47, 31),
    (8, 56, 4, 52, 11, 59, 7, 55),
    (40, 24, 36, 20, 43, 27, 39, 23),
    (2, 50, 14, 62, 1, 49, 13, 61),
    (34, 18, 46, 30, 33, 17, 45, 29),
    (10, 58, 6, 54, 9, 57, 5, 53),
    (42, 26, 38, 22, 41, 25, 37, 21),
)
BLUR_KERNEL = (1, 4, 6, 4, 1)
BLUR_DIVISOR = sum(BLUR_KERNEL)


def blur_tones(tones):
    """Apply a compact Gaussian coverage blur to reduce stair-step edges."""
    horizontal = [[0.0] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            total = 0.0
            for offset, weight in zip(range(-2, 3), BLUR_KERNEL):
                sample_x = min(SCREEN_WIDTH - 1, max(0, x + offset))
                total += tones[y][sample_x] * weight
            horizontal[y][x] = total / BLUR_DIVISOR

    blurred = [[0.0] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            total = 0.0
            for offset, weight in zip(range(-2, 3), BLUR_KERNEL):
                sample_y = min(SCREEN_HEIGHT - 1, max(0, y + offset))
                total += horizontal[sample_y][x] * weight
            blurred[y][x] = total / BLUR_DIVISOR
    return blurred


def main() -> None:
    width, height, rows = decode_png(PNG_PATH)
    left, top, right, bottom = content_bbox(width, height, rows)
    crop_width = right - left
    crop_height = bottom - top

    tones = [[0.0] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
    for y in range(CONTENT_TOP, CONTENT_TOP + CONTENT_HEIGHT):
        source_y = y - CONTENT_TOP
        sy0 = top + source_y * crop_height / CONTENT_HEIGHT
        sy1 = top + (source_y + 1) * crop_height / CONTENT_HEIGHT
        for x in range(CONTENT_LEFT, CONTENT_LEFT + CONTENT_WIDTH):
            source_x = x - CONTENT_LEFT
            sx0 = left + source_x * crop_width / CONTENT_WIDTH
            sx1 = left + (source_x + 1) * crop_width / CONTENT_WIDTH
            r, g, b, a = sample_area(rows, sx0, sy0, sx1, sy1)
            if a > 128:
                tones[y][x] = display_tone((r, g, b))

    blurred = blur_tones(tones)
    ink = [[False] * SCREEN_WIDTH for _ in range(SCREEN_HEIGHT)]
    for y in range(SCREEN_HEIGHT):
        for x in range(SCREEN_WIDTH):
            # Broad letter faces stay solid, but a bright pixel is considered
            # interior only when its immediate neighbours are also bright.
            # This prevents the source's block-stepped boundary from bypassing
            # the softened coverage map.
            tone = tones[y][x] * 0.35 + blurred[y][x] * 0.65
            neighbours = (
                tones[min(SCREEN_HEIGHT - 1, max(0, y + dy))]
                     [min(SCREEN_WIDTH - 1, max(0, x + dx))]
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if tones[y][x] >= 250 and all(value >= 220 for value in neighbours):
                tone = 255
            threshold = (BAYER_8X8[y & 7][x & 7] + 0.5) * 4
            ink[y][x] = tone > threshold

    bitmap = bytearray()
    for char_row in range(SCREEN_HEIGHT // 8):
        for char_col in range(SCREEN_WIDTH // 8):
            for line in range(8):
                value = 0xFF
                for bit in range(8):
                    if ink[char_row * 8 + line][char_col * 8 + bit]:
                        value &= ~(0x80 >> bit)
                bitmap.append(value)

    expected_size = SCREEN_WIDTH * SCREEN_HEIGHT // 8
    if len(bitmap) != expected_size:
        raise SystemExit(f"expected {expected_size} bitmap bytes, got {len(bitmap)}")
    OUT_PATH.write_bytes(bitmap)
    PRG_OUT_PATH.write_bytes(bytes((0x00, 0x78)) + bitmap)
    print(
        f"Wrote {OUT_PATH.relative_to(ROOT)} ({width}x{height} source, "
        f"crop={crop_width}x{crop_height}@{left},{top}, "
        f"output={SCREEN_WIDTH}x{SCREEN_HEIGHT}, {len(bitmap)} bytes)"
    )


if __name__ == "__main__":
    main()
