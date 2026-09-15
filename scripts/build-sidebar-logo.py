#!/usr/bin/env python3

"""Build a cell-aligned, six-color gameplay logo from the Sixies font."""

import pathlib
import sys


WIDTH = 80
HEIGHT = 32
GLYPH_SIZE = 16
GLYPH_BYTES = 32
TEXT = "SIXIES"
LETTER_WIDTHS = (16, 8, 16, 8, 8, 16)
CELL_COLORS = (0, 7, 7, 4, 13, 13, 11, 8, 10, 10)
C64_PALETTE = (
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
)


def glyph(font, character):
    offset = (ord(character) - ord("A")) * GLYPH_BYTES
    data = font[offset:offset + GLYPH_BYTES]
    return [
        [
            (data[y * 2 + x // 8] >> (7 - (x & 7))) & 1
            for x in range(GLYPH_SIZE)
        ]
        for y in range(GLYPH_SIZE)
    ]


def build_canvas(font):
    canvas = [[0] * WIDTH for _ in range(HEIGHT)]
    # Column zero shares the board's right-edge cell and is redrawn by the
    # grid renderer, so keep it empty and begin the logo at column one.
    origin_x = 8
    for character, width in zip(TEXT, LETTER_WIDTHS):
        pixels = glyph(font, character)
        for target_y in range(24):
            source_y = target_y * GLYPH_SIZE // 24
            for target_x in range(width):
                if width == 16:
                    value = pixels[source_y][target_x]
                elif character == "I":
                    value = pixels[source_y][target_x + 4]
                else:
                    source_x = target_x * 2
                    value = pixels[source_y][source_x] | pixels[source_y][source_x + 1]
                canvas[target_y + 4][origin_x + target_x] = value
        origin_x += width
    return canvas


def encode(canvas):
    bitmap = bytearray()
    screen = bytearray()
    preview = bytearray(WIDTH * HEIGHT * 3)
    for cell_y in range(HEIGHT // 8):
        for cell_x in range(WIDTH // 8):
            color = CELL_COLORS[cell_x]
            screen.append(color << 4)
            for row in range(8):
                value = 0
                y = cell_y * 8 + row
                for column in range(8):
                    x = cell_x * 8 + column
                    value = (value << 1) | canvas[y][x]
                    rgb = C64_PALETTE[color if canvas[y][x] else 0]
                    offset = (y * WIDTH + x) * 3
                    preview[offset:offset + 3] = bytes(rgb)
                bitmap.append(value)
    return bitmap, screen, preview


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-sidebar-logo.py FONT16.bin OUTPUT_DIRECTORY")
    font = pathlib.Path(sys.argv[1]).read_bytes()
    if len(font) != 36 * GLYPH_BYTES:
        raise ValueError("expected the 1152-byte Sixies 16x16 font")
    bitmap, screen, preview = encode(build_canvas(font))
    output = pathlib.Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    (output / "sidebar_logo_bitmap.bin").write_bytes(bitmap)
    (output / "sidebar_logo_screen.bin").write_bytes(screen)
    with (output / "sidebar_logo_preview.ppm").open("wb") as file:
        file.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        file.write(preview)
    print("Created cell-aligned 80x32 Sixies sidebar logo")


if __name__ == "__main__":
    main()
