#!/usr/bin/env python3
"""Extract the reusable texture and palette tables from the Razor plasma data."""

from pathlib import Path
import math
import re

ROOT = Path(__file__).resolve().parent.parent
BITMAP_PATH = ROOT / "src" / "assets" / "plasma" / "razor_combinedbitmap.csv.txt"
COLOR_PATH = ROOT / "src" / "assets" / "plasma" / "razor_color_plasma.txt"
SCREEN_PATH = ROOT / "src" / "assets" / "plasma" / "razor_screen_plasma.txt"
OUT_PATH = ROOT / "src" / "generated" / "razor_plasma.inc"
RIPPLE_PATH = ROOT / "src" / "generated" / "water_ripple_field.bin"


def parse_c64_bytes(path: Path) -> bytes:
    values = re.findall(r"\$([0-9a-fA-F]{2})", path.read_text(encoding="ascii"))
    return bytes(int(value, 16) for value in values)


def byte_lines(label: str, values: bytes) -> list[str]:
    encoded = ",".join(f"${value:02x}" for value in values)
    return [f"{label}:", f"!byte {encoded}"]


def main() -> None:
    combined = parse_c64_bytes(BITMAP_PATH)
    color = parse_c64_bytes(COLOR_PATH)
    screen = parse_c64_bytes(SCREEN_PATH)
    if len(combined) != 8000:
        raise SystemExit(f"expected 8000 Razor bitmap bytes, got {len(combined)}")
    if len(color) != 16 or len(screen) != 16:
        raise SystemExit("Razor color and screen tables must contain 16 bytes")

    # The first two character cells are the repeating plasma field. The rest
    # of the supplied bitmap contains unrelated artwork and is not imported.
    source_tile = combined[:16]
    for char_row in range(25):
        start = char_row * 320
        if combined[start:start + 16] != source_tile:
            raise SystemExit(f"Razor plasma tile changes at character row {char_row}")

    # Keep each filled disc inside one 8x8 color cell so an adjacent palette
    # value cannot erase half of it. The assembly initializer staggers these
    # complete cells over the display with blank cells between them.
    circle = bytes((0x00, 0x3c, 0xfc, 0xff, 0xff, 0x3f, 0x3c, 0x00))
    tile = circle

    lines = ["; Generated from the supplied Razor plasma tables."]
    lines += byte_lines("razor_plasma_bitmap_tile", tile)
    lines += byte_lines("razor_plasma_screen", screen)
    lines += byte_lines("razor_plasma_color", color)
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")

    # Pack two radial distance fields into each screen cell. Multiplying the
    # Euclidean distance by two gives several visible rings across 40 columns.
    centers = ((10.0, 7.0), (29.0, 17.0))
    ripple = bytearray()
    for y in range(25):
        for x in range(40):
            phases = [
                int(round(math.hypot(x - cx, y - cy) * 2.0)) & 0x0f
                for cx, cy in centers
            ]
            ripple.append(phases[0] | (phases[1] << 4))
    RIPPLE_PATH.write_bytes(ripple)
    print("Wrote Razor texture/palette tables and 1000-byte water ripple field")


if __name__ == "__main__":
    main()
