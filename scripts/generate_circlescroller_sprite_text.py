#!/usr/bin/env python3
"""Generate the 8-sprite CircleScroller text strip.

The runtime displays sprites 0-3 as the top row and sprites 4-7 as the bottom
row. Each C64 hires sprite is 24x21 pixels, stored as 21 rows of 3 bytes plus
one unused byte.
"""

from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/assets/circlescroller_turn_disk_sprites.bin"

SPRITES_ACROSS = 4
SPRITE_W = 24
SPRITE_H = 21
CANVAS_W = SPRITES_ACROSS * SPRITE_W
CANVAS_H = 2 * SPRITE_H
SCALE = 2
ROW_GAP = 1

TEXT_LINES = ("RETRO DNA", "'26")

FONT = {
    " ": ["0000", "0000", "0000", "0000", "0000", "0000", "0000"],
    "'": ["10", "10", "00", "00", "00", "00", "00"],
    "0": ["1111", "1001", "1001", "1001", "1001", "1001", "1111"],
    "1": ["0010", "0110", "0010", "0010", "0010", "0010", "0111"],
    "2": ["1110", "0001", "0001", "1110", "1000", "1000", "1111"],
    "3": ["1110", "0001", "0001", "0110", "0001", "0001", "1110"],
    "4": ["1001", "1001", "1001", "1111", "0001", "0001", "0001"],
    "5": ["1111", "1000", "1000", "1110", "0001", "0001", "1110"],
    "6": ["0111", "1000", "1000", "1110", "1001", "1001", "1110"],
    "7": ["1111", "0001", "0010", "0010", "0100", "0100", "0100"],
    "8": ["1110", "1001", "1001", "1110", "1001", "1001", "1110"],
    "9": ["1110", "1001", "1001", "1111", "0001", "0001", "1110"],
    "A": ["0110", "1001", "1001", "1111", "1001", "1001", "1001"],
    "B": ["1110", "1001", "1001", "1110", "1001", "1001", "1110"],
    "C": ["0111", "1000", "1000", "1000", "1000", "1000", "0111"],
    "D": ["1110", "1001", "1001", "1001", "1001", "1001", "1110"],
    "E": ["1111", "1000", "1000", "1110", "1000", "1000", "1111"],
    "F": ["1111", "1000", "1000", "1110", "1000", "1000", "1000"],
    "G": ["0111", "1000", "1000", "1011", "1001", "1001", "0111"],
    "H": ["1001", "1001", "1001", "1111", "1001", "1001", "1001"],
    "I": ["1110", "0100", "0100", "0100", "0100", "0100", "1110"],
    "J": ["0011", "0001", "0001", "0001", "1001", "1001", "0110"],
    "K": ["1001", "1010", "1100", "1000", "1100", "1010", "1001"],
    "L": ["1000", "1000", "1000", "1000", "1000", "1000", "1111"],
    "M": ["1001", "1111", "1111", "1001", "1001", "1001", "1001"],
    "N": ["1001", "1101", "1101", "1011", "1011", "1001", "1001"],
    "O": ["0110", "1001", "1001", "1001", "1001", "1001", "0110"],
    "P": ["1110", "1001", "1001", "1110", "1000", "1000", "1000"],
    "Q": ["0110", "1001", "1001", "1001", "1011", "1010", "0111"],
    "R": ["1110", "1001", "1001", "1110", "1100", "1010", "1001"],
    "S": ["0111", "1000", "1000", "0110", "0001", "0001", "1110"],
    "T": ["1111", "0100", "0100", "0100", "0100", "0100", "0100"],
    "U": ["1001", "1001", "1001", "1001", "1001", "1001", "0110"],
    "V": ["1001", "1001", "1001", "1001", "1001", "0110", "0110"],
    "W": ["1001", "1001", "1001", "1001", "1111", "1111", "1001"],
    "X": ["1001", "1001", "0110", "0110", "0110", "1001", "1001"],
    "Y": ["1001", "1001", "1001", "0110", "0100", "0100", "0100"],
    "Z": ["1111", "0001", "0010", "0010", "0100", "1000", "1111"],
}


def text_width(text: str) -> int:
    width = 0
    for index, char in enumerate(text.upper()):
        glyph = FONT[char]
        width += len(glyph[0]) * SCALE
        if index != len(text) - 1:
            width += SCALE
    return width


def draw_text(canvas: list[list[int]], text: str, x: int, y: int) -> None:
    cursor_x = x
    for index, char in enumerate(text.upper()):
        glyph = FONT[char]
        for glyph_y, row in enumerate(glyph):
            for glyph_x, pixel in enumerate(row):
                if pixel == "0":
                    continue
                for sy in range(SCALE):
                    for sx in range(SCALE):
                        px = cursor_x + glyph_x * SCALE + sx
                        py = y + glyph_y * SCALE + sy
                        if 0 <= px < CANVAS_W and 0 <= py < CANVAS_H:
                            canvas[py][px] = 1
        cursor_x += len(glyph[0]) * SCALE
        if index != len(text) - 1:
            cursor_x += SCALE


def pack_sprites(canvas: list[list[int]]) -> bytes:
    output = bytearray()
    for sprite_index in range(8):
        sprite_x = (sprite_index % SPRITES_ACROSS) * SPRITE_W
        sprite_y = (sprite_index // SPRITES_ACROSS) * SPRITE_H
        for y in range(SPRITE_H):
            for byte_index in range(3):
                value = 0
                for bit in range(8):
                    px = sprite_x + byte_index * 8 + bit
                    py = sprite_y + y
                    if canvas[py][px]:
                        value |= 1 << (7 - bit)
                output.append(value)
        output.append(0)
    return bytes(output)


def render_ascii(canvas: list[list[int]]) -> str:
    lines = []
    for y in range(0, CANVAS_H, ROW_GAP):
        lines.append("".join("#" if value else "." for value in canvas[y]))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="print an ASCII preview")
    args = parser.parse_args()

    canvas = [[0 for _ in range(CANVAS_W)] for _ in range(CANVAS_H)]
    for line_index, text in enumerate(TEXT_LINES):
        width = text_width(text)
        x = (CANVAS_W - width) // 2
        y = line_index * SPRITE_H + (SPRITE_H - 7 * SCALE) // 2
        draw_text(canvas, text, x, y)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(pack_sprites(canvas))
    print(f"Wrote {OUT}")
    if args.preview:
        print(render_ascii(canvas))


if __name__ == "__main__":
    main()
