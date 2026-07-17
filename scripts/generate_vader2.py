#!/usr/bin/env python3
"""Convert vader2 artwork to a perspective-preserving C64 hires image."""

import binascii
from pathlib import Path
import struct
import zlib

from generate_logo import BAYER_4X4, decode_png, display_tone, sample_area


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "assets" / "vader2_source.png"
PREVIEW_OUT = ROOT / "src" / "assets" / "vader2.png"
BITMAP_OUT = ROOT / "src" / "generated" / "vader2_hires_bitmap.bin"
SCREEN_OUT = ROOT / "src" / "generated" / "vader2_hires_screen.bin"

WIDTH = 320
HEIGHT = 200
# Colodore-style C64 palette, indexed exactly as the VIC-II color registers.
PALETTE = (
    (0, 0, 0), (255, 255, 255), (136, 57, 50), (103, 182, 189),
    (139, 63, 150), (85, 160, 73), (64, 49, 141), (191, 206, 114),
    (139, 84, 41), (87, 66, 0), (184, 105, 98), (80, 80, 80),
    (120, 120, 120), (148, 224, 137), (120, 105, 196), (159, 159, 159),
)

# Vader is rendered as a black/gray hires portrait. Keeping the ink ramp
# monochrome avoids C64 8x8 color-cell stair steps showing up as purple/blue
# right angles across the helmet. Pure white is deliberately excluded: white
# highlights are carried by dither density instead of 8x8 cell color changes.
VADER_INKS = (11, 12, 15)


def color_error(left, right):
    return ((left[0] - right[0]) ** 2 * 2
            + (left[1] - right[1]) ** 2 * 3
            + (left[2] - right[2]) ** 2)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = binascii.crc32(kind + payload) & 0xffffffff
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def write_rgb_png(path: Path, rows) -> None:
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in rows)
    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )


def main() -> None:
    source_width, source_height, source_rows = decode_png(SOURCE)
    scaled_width = round(source_width * HEIGHT / source_height)

    # Fit the complete source frame by height. No crop, skew, or row-wise
    # realignment is applied, so the original helmet perspective is retained.
    pixels = [[PALETTE[0]] * WIDTH for _ in range(HEIGHT)]
    for y in range(HEIGHT):
        sy0 = y * source_height / HEIGHT
        sy1 = (y + 1) * source_height / HEIGHT
        for x in range(scaled_width):
            sx0 = x * source_width / scaled_width
            sx1 = (x + 1) * source_width / scaled_width
            r, g, b, _ = sample_area(source_rows, sx0, sy0, sx1, sy1)
            pixels[y][x] = (r, g, b)

    bitmap = bytearray(8000)
    screen = bytearray(1000)
    rendered = [[PALETTE[0]] * WIDTH for _ in range(HEIGHT)]
    for cell_y in range(25):
        for cell_x in range(40):
            samples = [
                pixels[cell_y * 8 + y][cell_x * 8 + x]
                for y in range(8) for x in range(8)
            ]
            ink_mask = []
            ink_samples = []
            for y in range(8):
                for x in range(8):
                    pixel = samples[y * 8 + x]
                    threshold = (BAYER_4X4[(cell_y * 8 + y) & 3]
                                           [(cell_x * 8 + x) & 3] + 0.5) * 16
                    is_ink = display_tone(pixel) > threshold
                    ink_mask.append(is_ink)
                    if is_ink:
                        ink_samples.append(pixel)

            if ink_samples:
                tone = sum(display_tone(pixel) for pixel in ink_samples) / len(ink_samples)
                # Keep bright highlights on light gray. The bitmap density
                # still carries the highlight, but hard white cell corners do
                # not appear on the curved helmet.
                if tone >= 132:
                    ink = 15
                elif tone >= 88:
                    ink = 12
                else:
                    ink = 11
            else:
                ink = 15
            screen[cell_y * 40 + cell_x] = ink << 4

            for y in range(8):
                byte = 0
                py = cell_y * 8 + y
                for x in range(8):
                    px = cell_x * 8 + x
                    is_ink = ink_mask[y * 8 + x]
                    if is_ink:
                        byte |= 0x80 >> x
                    rendered[py][px] = PALETTE[ink] if is_ink else PALETTE[0]
                bitmap[cell_y * 320 + cell_x * 8 + y] = byte

    PREVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    BITMAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_rgb_png(PREVIEW_OUT, rendered)
    BITMAP_OUT.write_bytes(bitmap)
    SCREEN_OUT.write_bytes(screen)
    print(
        f"Wrote {PREVIEW_OUT.relative_to(ROOT)} ({WIDTH}x{HEIGHT}, "
        f"source fit {scaled_width}x{HEIGHT}), {len(bitmap)} bitmap bytes, "
        f"and {len(screen)} screen bytes"
    )


if __name__ == "__main__":
    main()
