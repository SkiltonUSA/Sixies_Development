#!/usr/bin/env python3

"""Convert the chain-reaction artwork into three native hi-res C64 sprites."""

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
THRESHOLD = 88


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


def luminance(rgb, pixel):
    offset = pixel * 3
    red, green, blue = rgb[offset:offset + 3]
    return (77 * red + 150 * green + 29 * blue) >> 8


def artwork_bounds(rgb, width, height):
    left, top = width, height
    right = bottom = -1
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 3
            if max(rgb[offset:offset + 3]) < 16:
                continue
            left = min(left, x)
            top = min(top, y)
            right = max(right, x)
            bottom = max(bottom, y)
    if right < left:
        raise ValueError("chain-reaction artwork is empty")
    return left, top, right + 1, bottom + 1


def reduce_to_sprite_composite(rgb, width, height):
    left, top, right, bottom = artwork_bounds(rgb, width, height)
    source_width = right - left
    source_height = bottom - top
    pixels = bytearray(COMPOSITE_WIDTH * COMPOSITE_HEIGHT)

    for target_y in range(COMPOSITE_HEIGHT):
        source_y0 = top + target_y * source_height // COMPOSITE_HEIGHT
        source_y1 = top + (target_y + 1) * source_height // COMPOSITE_HEIGHT
        for target_x in range(COMPOSITE_WIDTH):
            source_x0 = left + target_x * source_width // COMPOSITE_WIDTH
            source_x1 = left + (target_x + 1) * source_width // COMPOSITE_WIDTH
            total = 0
            samples = 0
            for source_y in range(source_y0, max(source_y0 + 1, source_y1)):
                row = source_y * width
                for source_x in range(source_x0, max(source_x0 + 1, source_x1)):
                    total += luminance(rgb, row + source_x)
                    samples += 1
            pixels[target_y * COMPOSITE_WIDTH + target_x] = total // samples >= THRESHOLD
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
    scale = 4
    width = COMPOSITE_WIDTH * scale
    height = COMPOSITE_HEIGHT * scale
    preview = bytearray(width * height * 3)

    for y in range(height):
        source_y = y // scale
        for x in range(width):
            source_x = x // scale
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
    pixels = reduce_to_sprite_composite(rgb, width, height)
    sprite_data = build_sprites(pixels)
    (output_directory / "chain_reaction_sprite.bin").write_bytes(sprite_data)
    write_preview(pixels, output_directory / "chain_reaction_preview.ppm")
    print(f"Built {SPRITE_COUNT} chain-reaction sprites ({len(sprite_data)} bytes)")


if __name__ == "__main__":
    main()
