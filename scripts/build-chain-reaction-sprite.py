#!/usr/bin/env python3

"""Convert the chain-reaction artwork into three expanded hi-res C64 sprites."""

import pathlib
import struct
import subprocess
import sys


SPRITE_COLUMNS = 3
SPRITE_ROWS = 1
SPRITE_COUNT = SPRITE_COLUMNS * SPRITE_ROWS
SPRITE_WIDTH = 24
SPRITE_HEIGHT = 21
COMPOSITE_WIDTH = SPRITE_COLUMNS * SPRITE_WIDTH
COMPOSITE_HEIGHT = SPRITE_ROWS * SPRITE_HEIGHT
DISPLAY_SCALE_X = 1
DISPLAY_SCALE_Y = 2
EXPECTED_SOURCE_SIZE = (77, 39)
SOURCE_LEFT = 2
SOURCE_RIGHT = 75
ARTWORK_WIDTH = 72
ARTWORK_HEIGHT = 20
ARTWORK_LEFT = (COMPOSITE_WIDTH - ARTWORK_WIDTH) // 2
ARTWORK_TOP = (COMPOSITE_HEIGHT - ARTWORK_HEIGHT) // 2

# The supplied image is an excellent shape reference, but its antialiased
# lettering becomes too thin after the image is reduced to the VIC-II's
# 72x20 logical sprite grid.  Replace only the lettering with a deliberately
# chunky 5x7 pixel alphabet cut out of a solid white callout. Hardware Y
# expansion restores the artwork to 72x40 on screen, while the filled badge
# separates the words from the colorful mascot beneath it.
PIXEL_FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}


def load_png_rgb(path):
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG image")
    width, height = struct.unpack(">II", header[16:24])
    rgb = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    if len(rgb) != width * height * 3:
        raise ValueError(f"could not decode all pixels from {path}")
    return rgb, width, height


def is_artwork_pixel(rgb, pixel):
    """Keep the pale-green callout fill off its neutral-gray source matte."""
    offset = pixel * 3
    red, green, blue = rgb[offset:offset + 3]
    return green >= red + 4 and green >= blue + 4


def reduce_artwork_fill(rgb, width, height):
    """Reduce the source callout fill to the logical 72x20 sprite grid."""
    fill = bytearray(ARTWORK_WIDTH * ARTWORK_HEIGHT)
    # The source is 77x39 with a two-pixel neutral matte at each horizontal
    # edge. Preserve its 72-pixel artwork width, halve only the height, and
    # use VIC-II Y expansion to restore the original 40-pixel footprint.
    source_width = SOURCE_RIGHT - SOURCE_LEFT
    for target_y in range(ARTWORK_HEIGHT):
        source_y0 = target_y * height // ARTWORK_HEIGHT
        source_y1 = (target_y + 1) * height // ARTWORK_HEIGHT
        for target_x in range(ARTWORK_WIDTH):
            source_x0 = SOURCE_LEFT + target_x * source_width // ARTWORK_WIDTH
            source_x1 = SOURCE_LEFT + (target_x + 1) * source_width // ARTWORK_WIDTH
            artwork_samples = 0
            samples = 0
            for source_y in range(source_y0, max(source_y0 + 1, source_y1)):
                row = source_y * width
                for source_x in range(source_x0, max(source_x0 + 1, source_x1)):
                    artwork_samples += is_artwork_pixel(rgb, row + source_x)
                    samples += 1
            if artwork_samples * 2 >= samples:
                fill[target_y * ARTWORK_WIDTH + target_x] = 1
    return fill


def fill_enclosed_gaps(fill):
    """Fill the source's original lettering without changing its silhouette."""
    outside = bytearray(len(fill))
    pending = []

    def queue(x, y):
        offset = y * ARTWORK_WIDTH + x
        if not fill[offset] and not outside[offset]:
            outside[offset] = 1
            pending.append((x, y))

    for x in range(ARTWORK_WIDTH):
        queue(x, 0)
        queue(x, ARTWORK_HEIGHT - 1)
    for y in range(ARTWORK_HEIGHT):
        queue(0, y)
        queue(ARTWORK_WIDTH - 1, y)

    while pending:
        x, y = pending.pop()
        if x:
            queue(x - 1, y)
        if x + 1 < ARTWORK_WIDTH:
            queue(x + 1, y)
        if y:
            queue(x, y - 1)
        if y + 1 < ARTWORK_HEIGHT:
            queue(x, y + 1)

    return bytearray(0 if outside[offset] else 1 for offset in range(len(fill)))


def draw_centered_text(pixels, text, top, pixel_value):
    width = len(text) * 5 + len(text) - 1
    left = (COMPOSITE_WIDTH - width) // 2
    for character_index, character in enumerate(text):
        glyph = PIXEL_FONT[character]
        glyph_left = left + character_index * 6
        for glyph_y, row in enumerate(glyph):
            for glyph_x, glyph_pixel in enumerate(row):
                if glyph_pixel == "1":
                    pixels[(top + glyph_y) * COMPOSITE_WIDTH
                           + glyph_left + glyph_x] = pixel_value


def reduce_to_sprite_composite(rgb, width, height):
    fill = reduce_artwork_fill(rgb, width, height)
    silhouette = fill_enclosed_gaps(fill)
    pixels = bytearray(COMPOSITE_WIDTH * COMPOSITE_HEIGHT)

    for y in range(ARTWORK_HEIGHT):
        for x in range(ARTWORK_WIDTH):
            if silhouette[y * ARTWORK_WIDTH + x]:
                pixels[(ARTWORK_TOP + y) * COMPOSITE_WIDTH
                       + ARTWORK_LEFT + x] = 1

    draw_centered_text(pixels, "CHAIN", 2, 0)
    draw_centered_text(pixels, "REACTION!", 11, 0)
    return pixels


def build_sprites(pixels):
    output = bytearray()
    for sprite in range(SPRITE_COUNT):
        sprite_x = (sprite % SPRITE_COLUMNS) * SPRITE_WIDTH
        sprite_y = (sprite // SPRITE_COLUMNS) * SPRITE_HEIGHT
        for y in range(SPRITE_HEIGHT):
            for byte_index in range(3):
                value = 0
                for bit in range(8):
                    x = sprite_x + byte_index * 8 + bit
                    if pixels[(sprite_y + y) * COMPOSITE_WIDTH + x]:
                        value |= 0x80 >> bit
                output.append(value)
        output.append(0)
    return output


def write_preview(pixels, destination):
    width = COMPOSITE_WIDTH * DISPLAY_SCALE_X
    height = COMPOSITE_HEIGHT * DISPLAY_SCALE_Y
    preview = bytearray(width * height * 3)

    for y in range(height):
        source_y = y // DISPLAY_SCALE_Y
        for x in range(width):
            source_x = x // DISPLAY_SCALE_X
            color = (0, 0, 0)
            if pixels[source_y * COMPOSITE_WIDTH + source_x]:
                color = (255, 255, 255)
            offset = (y * width + x) * 3
            preview[offset:offset + 3] = bytes(color)
    destination.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + preview)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-chain-reaction-sprite.py SOURCE_PNG OUTPUT_DIRECTORY")
    source = pathlib.Path(sys.argv[1])
    output_directory = pathlib.Path(sys.argv[2])
    output_directory.mkdir(parents=True, exist_ok=True)

    rgb, width, height = load_png_rgb(source)
    if (width, height) != EXPECTED_SOURCE_SIZE:
        raise ValueError(
            f"chain-reaction master must be {EXPECTED_SOURCE_SIZE[0]}x"
            f"{EXPECTED_SOURCE_SIZE[1]}, got {width}x{height}"
        )
    pixels = reduce_to_sprite_composite(rgb, width, height)
    sprite_data = build_sprites(pixels)
    (output_directory / "chain_reaction_sprite.bin").write_bytes(sprite_data)
    write_preview(pixels, output_directory / "chain_reaction_preview.ppm")
    print(
        f"Built {SPRITE_COUNT} expanded chain-reaction sprites "
        f"({len(sprite_data)} bytes, {ARTWORK_WIDTH * DISPLAY_SCALE_X}x"
        f"{ARTWORK_HEIGHT * DISPLAY_SCALE_Y} displayed artwork)"
    )


if __name__ == "__main__":
    main()
