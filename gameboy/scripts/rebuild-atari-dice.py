#!/usr/bin/env python3

from collections import deque
from pathlib import Path
import re

from PIL import Image

from dice_shading import FACE_SHADES


ROOT = Path(__file__).resolve().parents[1]
ATARI = ROOT.parent / "atari8" / "assets" / "dice"
DICE = ROOT / "assets" / "dice"
PALETTE = ((229, 240, 183), (139, 172, 15), (48, 98, 48), (13, 56, 0))
FACE_NAMES = ("one", "two", "three", "four", "five", "six")
FACE_STYLES = (
    (1, 2, 3), (1, 3, 2), (2, 1, 3),
    (2, 3, 1), (3, 1, 2), (3, 2, 1),
)


def load_atari_die(name):
    source = (ATARI / f"die_{name}.asm").read_text()
    values = [int(value, 16) for value in re.findall(r"\$([0-9a-fA-F]{2})(?![0-9a-fA-F])", source)]
    if len(values) != 64 or values[60:] != [0, 0, 0, 0]:
        raise ValueError(f"invalid Atari die source: {name}")
    image = Image.new("1", (24, 20), 0)
    for row in range(20):
        for column in range(24):
            if values[row * 3 + column // 8] & (0x80 >> (column & 7)):
                image.putpixel((column, row), 1)
    return image.resize((16, 16), Image.Resampling.NEAREST)


def exterior_pixels(image):
    exterior = set()
    pending = deque()
    for coordinate in ((column, row) for row in range(16) for column in range(16)
                       if column in (0, 15) or row in (0, 15)):
        if not image.getpixel(coordinate):
            exterior.add(coordinate)
            pending.append(coordinate)
    while pending:
        column, row = pending.popleft()
        for delta_x, delta_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = column + delta_x, row + delta_y
            if not (0 <= neighbor[0] < 16 and 0 <= neighbor[1] < 16):
                continue
            if neighbor not in exterior and not image.getpixel(neighbor):
                exterior.add(neighbor)
                pending.append(neighbor)
    return exterior


def reference_die(face):
    image = load_atari_die(FACE_NAMES[face])
    exterior = exterior_pixels(image)
    style = FACE_STYLES[face]
    result = Image.new("L", (18, 18), 0)
    for row in range(16):
        for column in range(16):
            coordinate = (column, row)
            if coordinate in exterior:
                continue
            if not image.getpixel(coordinate):
                shade = style[2]
            elif column in (0, 15) or row in (0, 15) or any(
                (column + delta_x, row + delta_y) in exterior
                for delta_x, delta_y in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                shade = style[1]
            else:
                shade = style[0]
            result.putpixel((column + 1, row + 1), shade)
    return result


def source_die(face):
    inverse_shades = tuple(FACE_SHADES[face].index(shade) for shade in range(4))
    indexed = reference_die(face)
    source = Image.new("RGBA", indexed.size)
    for row in range(18):
        for column in range(18):
            shade = indexed.getpixel((column, row))
            if shade:
                source.putpixel((column, row), PALETTE[inverse_shades[shade]] + (255,))
    return source


def main():
    for face, name in enumerate(FACE_NAMES):
        source_die(face).save(DICE / f"{name}_18x18.png")


if __name__ == "__main__":
    main()
