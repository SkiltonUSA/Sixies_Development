#!/usr/bin/env python3

"""Derive the compact gameplay logo from the converted credits logo."""

from pathlib import Path
import sys


SOURCE_WIDTH = 128
SOURCE_HEIGHT = 40
TARGET_WIDTH = 96
TARGET_HEIGHT = 16
HORIZONTAL_PADDING = 2
BLACK = (0x00, 0x00, 0x00)
LIGHT_GREEN = (0xA9, 0xFF, 0x9F)


def decode_bitmap(data: bytes) -> list[list[int]]:
    expected = SOURCE_WIDTH * SOURCE_HEIGHT // 8
    if len(data) != expected:
        raise ValueError(f"expected a {expected}-byte 128x40 hi-res bitmap")
    pixels = [[0] * SOURCE_WIDTH for _ in range(SOURCE_HEIGHT)]
    cells_wide = SOURCE_WIDTH // 8
    for cell_y in range(SOURCE_HEIGHT // 8):
        for cell_x in range(cells_wide):
            for row in range(8):
                value = data[(cell_y * cells_wide + cell_x) * 8 + row]
                for column in range(8):
                    pixels[cell_y * 8 + row][cell_x * 8 + column] = (
                        value >> (7 - column)
                    ) & 1
    return pixels


def content_bounds(pixels: list[list[int]]) -> tuple[int, int, int, int]:
    points = [
        (x, y)
        for y, row in enumerate(pixels)
        for x, value in enumerate(row)
        if value
    ]
    if not points:
        raise ValueError("credits logo bitmap contains no foreground pixels")
    left = max(0, min(x for x, _ in points) - HORIZONTAL_PADDING)
    right = min(SOURCE_WIDTH, max(x for x, _ in points) + 1 + HORIZONTAL_PADDING)
    top = min(y for _, y in points)
    bottom = max(y for _, y in points) + 1
    return left, top, right, bottom


def resize(pixels: list[list[int]]) -> list[list[int]]:
    left, top, right, bottom = content_bounds(pixels)
    crop_width = right - left
    crop_height = bottom - top
    output = []
    for y in range(TARGET_HEIGHT):
        source_top = top + y * crop_height // TARGET_HEIGHT
        source_bottom = top + (y + 1) * crop_height // TARGET_HEIGHT
        source_bottom = max(source_top + 1, source_bottom)
        row = []
        for x in range(TARGET_WIDTH):
            source_x = left + x * crop_width // TARGET_WIDTH
            samples = [
                pixels[source_y][source_x]
                for source_y in range(source_top, source_bottom)
            ]
            row.append(int(sum(samples) * 2 >= len(samples)))
        output.append(row)
    return output


def encode_bitmap(pixels: list[list[int]]) -> bytes:
    output = bytearray()
    for cell_y in range(TARGET_HEIGHT // 8):
        for cell_x in range(TARGET_WIDTH // 8):
            for row in range(8):
                value = 0
                for column in range(8):
                    value = (value << 1) | pixels[cell_y * 8 + row][
                        cell_x * 8 + column
                    ]
                output.append(value)
    return bytes(output)


def encode_preview(pixels: list[list[int]]) -> bytes:
    output = bytearray()
    for row in pixels:
        for value in row:
            output.extend(LIGHT_GREEN if value else BLACK)
    return bytes(output)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: build-gameplay-logo.py CREDITS_LOGO_BITMAP.bin OUTPUT_DIRECTORY"
        )
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    pixels = resize(decode_bitmap(source.read_bytes()))
    output.mkdir(parents=True, exist_ok=True)
    (output / "gameplay_logo_bitmap.bin").write_bytes(encode_bitmap(pixels))
    with (output / "gameplay_logo_preview.ppm").open("wb") as preview:
        preview.write(f"P6\n{TARGET_WIDTH} {TARGET_HEIGHT}\n255\n".encode("ascii"))
        preview.write(encode_preview(pixels))
    print("Created 96x16 gameplay logo from the credits artwork")


if __name__ == "__main__":
    main()
