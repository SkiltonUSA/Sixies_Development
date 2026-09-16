#!/usr/bin/env python3

from collections import deque
from pathlib import Path

from PIL import Image

from dice_shading import FACE_SHADES


ROOT = Path(__file__).resolve().parents[1]
DICE = ROOT / "assets" / "dice"
REFERENCE = DICE / "reference_dice_master.png"
PALETTE = ((229, 240, 183), (139, 172, 15), (48, 98, 48), (13, 56, 0))
FACE_NAMES = ("one", "two", "three", "four", "five", "six")
FACE_STYLES = (
    (1, 2, 3), (1, 2, 3), (1, 2, 3),
    (1, 2, 3), (1, 2, 3), (1, 2, 3),
)


def flood_exterior(image, background):
    exterior = set()
    pending = deque()
    for coordinate in ((column, row) for row in range(16) for column in range(16)
                       if column in (0, 15) or row in (0, 15)):
        if image.getpixel(coordinate) == background:
            exterior.add(coordinate)
            pending.append(coordinate)
    while pending:
        column, row = pending.popleft()
        for delta_x, delta_y in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = column + delta_x, row + delta_y
            if not (0 <= neighbor[0] < 16 and 0 <= neighbor[1] < 16):
                continue
            if neighbor not in exterior and image.getpixel(neighbor) == background:
                exterior.add(neighbor)
                pending.append(neighbor)
    return exterior


def reference_die(face):
    with Image.open(REFERENCE) as master:
        image = master.convert("RGB").crop((16 + face * 256, 16, 176 + face * 256, 176))
    image = image.resize((16, 16), Image.Resampling.NEAREST)
    background = image.getpixel((0, 0))
    exterior = flood_exterior(image, background)
    style = FACE_STYLES[face]
    result = Image.new("L", (18, 18), 0)
    for row in range(16):
        for column in range(16):
            coordinate = (column, row)
            if coordinate in exterior:
                continue
            if image.getpixel(coordinate) == background:
                target_shade = style[2]
            elif column in (0, 15) or row in (0, 15) or any(
                (column + delta_x, row + delta_y) in exterior
                for delta_x, delta_y in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                target_shade = style[1]
            else:
                target_shade = style[0]
            result.putpixel((column + 1, row + 1), target_shade)
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
