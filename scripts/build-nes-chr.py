#!/usr/bin/env python3
"""Build the native Sixies NES background CHR bank."""

import argparse
from pathlib import Path

from nes_graphics import encode_tile, read_png


TILE_BYTES = 16
TILE_COUNT = 256
DIE_BASE = 92
DIE_SIZE = 24
DIE_TILES_PER_STYLE = 54
DIE_ASSET_DIR = Path(__file__).resolve().parents[1] / "ports/nes/assets/dice"

FONT = {
    " ": ("00000",) * 7,
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00100", "00100", "01000", "10000", "00000"),
    ":": ("00000", "00100", "00100", "00000", "00100", "00100", "00000"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


def font_tile(rows):
    pixels = [[0] * 8 for _ in range(8)]
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if value == "1":
                pixels[y][x + 1] = 1
    return encode_tile(pixels)


def grid_tile(horizontal, vertical):
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            if (horizontal and y in (3, 4)) or (vertical and x in (3, 4)):
                pixels[y][x] = 1
    return encode_tile(pixels)


def grid_junction(left, right, up, down):
    pixels = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            horizontal = y in (3, 4) and (
                (left and x <= 4) or (right and x >= 3)
            )
            vertical = x in (3, 4) and (
                (up and y <= 4) or (down and y >= 3)
            )
            if horizontal or vertical:
                pixels[y][x] = 1
    return encode_tile(pixels)


def largest_component(candidate):
    visited = set()
    largest = set()
    for y in range(DIE_SIZE):
        for x in range(DIE_SIZE):
            if not candidate[y][x] or (x, y) in visited:
                continue
            component = set()
            pending = [(x, y)]
            visited.add((x, y))
            while pending:
                current_x, current_y = pending.pop()
                component.add((current_x, current_y))
                for next_x, next_y in (
                    (current_x - 1, current_y), (current_x + 1, current_y),
                    (current_x, current_y - 1), (current_x, current_y + 1)
                ):
                    if (0 <= next_x < DIE_SIZE and 0 <= next_y < DIE_SIZE and
                            candidate[next_y][next_x] and
                            (next_x, next_y) not in visited):
                        visited.add((next_x, next_y))
                        pending.append((next_x, next_y))
            if len(component) > len(largest):
                largest = component
    return largest


def load_die_pixels(value):
    path = DIE_ASSET_DIR / f"dice_{value}_64x64.png"
    image = read_png(path)
    fill_color = 2 if value & 1 else 3
    samples = [[None] * DIE_SIZE for _ in range(DIE_SIZE)]
    candidate = [[False] * DIE_SIZE for _ in range(DIE_SIZE)]

    for y in range(DIE_SIZE):
        source_y = (2 * y + 1) * image.height // (2 * DIE_SIZE)
        for x in range(DIE_SIZE):
            source_x = (2 * x + 1) * image.width // (2 * DIE_SIZE)
            sample = image.pixels[source_y][source_x]
            samples[y][x] = sample
            red, green, blue, alpha = sample
            darkest = min(red, green, blue)
            lightest = max(red, green, blue)
            candidate[y][x] = (
                alpha >= 96 and lightest >= 70 and
                (lightest - darkest >= 30 or lightest >= 150)
            )

    face = largest_component(candidate)
    mask = [[False] * DIE_SIZE for _ in range(DIE_SIZE)]
    for y in range(DIE_SIZE):
        face_x = [x for x in range(DIE_SIZE) if (x, y) in face]
        if face_x:
            for x in range(min(face_x), max(face_x) + 1):
                mask[y][x] = True

    pixels = [[0] * DIE_SIZE for _ in range(DIE_SIZE)]
    for y in range(DIE_SIZE):
        for x in range(DIE_SIZE):
            if not mask[y][x]:
                continue
            red, green, blue, _ = samples[y][x]
            darkest = min(red, green, blue)
            lightest = max(red, green, blue)
            if lightest < 70:
                pixels[y][x] = 0
            elif lightest - darkest < 30:
                if value == 1 and lightest >= 150:
                    pixels[y][x] = fill_color
                else:
                    pixels[y][x] = 1
            else:
                pixels[y][x] = fill_color
    return pixels, mask


def is_boundary(mask, x, y):
    return mask[y][x] and any(
        nx < 0 or nx >= DIE_SIZE or ny < 0 or ny >= DIE_SIZE or not mask[ny][nx]
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
    )


def style_die(normal, mask, style):
    pixels = [row[:] for row in normal]
    for y in range(DIE_SIZE):
        for x in range(DIE_SIZE):
            if not mask[y][x]:
                pixels[y][x] = 0
            elif style == 1 and is_boundary(mask, x, y):
                pixels[y][x] = 1 if (x + y) % 2 == 0 else 0
            elif style == 2 and normal[y][x] != 0:
                pixels[y][x] = 2 if (x + y) % 2 == 0 else 0
    return pixels


def extract_tile(pixels, position):
    tile_x = position % 3
    tile_y = position // 3
    return encode_tile([
        row[tile_x * 8:(tile_x + 1) * 8]
        for row in pixels[tile_y * 8:(tile_y + 1) * 8]
    ])


def build_chr():
    tiles = [bytes(TILE_BYTES) for _ in range(TILE_COUNT)]
    tiles[1] = grid_tile(True, False)
    tiles[2] = grid_tile(False, True)
    tiles[3] = grid_tile(True, True)
    tiles[4] = grid_junction(True, True, False, True)
    tiles[5] = grid_junction(True, True, True, False)
    tiles[6] = grid_junction(False, True, True, True)
    tiles[7] = grid_junction(True, False, True, True)
    tiles[8] = grid_junction(False, True, False, True)
    tiles[9] = grid_junction(True, False, False, True)
    tiles[10] = grid_junction(False, True, True, False)
    tiles[11] = grid_junction(True, False, True, False)

    for character, rows in FONT.items():
        tiles[ord(character)] = font_tile(rows)

    for style in range(3):
        for value in range(1, 7):
            normal, mask = load_die_pixels(value)
            pixels = style_die(normal, mask, style)
            for position in range(9):
                index = (DIE_BASE + style * DIE_TILES_PER_STYLE +
                         (value - 1) * 9 + position)
                tiles[index] = extract_tile(pixels, position)
    return b"".join(tiles)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build_chr())
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
