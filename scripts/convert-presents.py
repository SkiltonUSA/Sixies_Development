#!/usr/bin/env python3

import pathlib
import sys


WIDTH = 320
HEIGHT = 200
PALETTE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
]


def pack(data):
    output = bytearray()
    index = 0
    while index < len(data):
        run = 1
        while index + run < len(data) and data[index + run] == data[index] and run < 127:
            run += 1
        if run >= 3:
            output.extend((0x80 | run, data[index]))
            index += run
            continue

        literal_start = index
        index += run
        while index < len(data) and index - literal_start < 127:
            next_run = 1
            while (
                index + next_run < len(data)
                and data[index + next_run] == data[index]
                and next_run < 127
            ):
                next_run += 1
            if next_run >= 3:
                break
            index += min(next_run, 127 - (index - literal_start))
        literal = data[literal_start:index]
        output.append(len(literal))
        output.extend(literal)
    output.append(0)
    return output


def render_preview(bitmap, screen, color_ram, background):
    preview = bytearray(WIDTH * HEIGHT * 3)
    for cell_y in range(25):
        for cell_x in range(40):
            cell = cell_y * 40 + cell_x
            colors = (
                background,
                screen[cell] >> 4,
                screen[cell] & 0x0f,
                color_ram[cell] & 0x0f,
            )
            for row in range(8):
                value = bitmap[cell * 8 + row]
                for pair in range(4):
                    color = PALETTE[colors[(value >> (6 - pair * 2)) & 3]]
                    x = cell_x * 8 + pair * 2
                    y = cell_y * 8 + row
                    for doubled_x in (x, x + 1):
                        offset = (y * WIDTH + doubled_x) * 3
                        preview[offset:offset + 3] = bytes(color)
    return preview


def expand_nibble(value):
    output = 0
    for bit in range(4):
        output = (output << 2) | (3 if value & (1 << (3 - bit)) else 0)
    return output


def draw_font16(bitmap, color_ram, font, text, cell_x, cell_y, color):
    for character_index, character in enumerate(text):
        if "A" <= character <= "Z":
            glyph_index = ord(character) - ord("A")
        elif "0" <= character <= "9":
            glyph_index = 26 + ord(character) - ord("0")
        else:
            raise ValueError(f"unsupported presents character {character!r}")
        glyph = font[glyph_index * 32:(glyph_index + 1) * 32]
        for glyph_y in range(16):
            source = (glyph[glyph_y * 2] << 8) | glyph[glyph_y * 2 + 1]
            logical = 0
            for pair in range(8):
                mask = 0xC000 >> (pair * 2)
                logical = (logical << 1) | int(bool(source & mask))
            row = cell_y + glyph_y // 8
            left_cell = row * 40 + cell_x + character_index * 2
            bitmap[left_cell * 8 + glyph_y % 8] = expand_nibble(logical >> 4)
            bitmap[(left_cell + 1) * 8 + glyph_y % 8] = expand_nibble(logical & 0x0f)
            color_ram[left_cell] = color
            color_ram[left_cell + 1] = color


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: convert-presents.py INPUT.kla FONT16.bin OUTPUT_DIRECTORY")
    source = pathlib.Path(sys.argv[1])
    font_path = pathlib.Path(sys.argv[2])
    output = pathlib.Path(sys.argv[3])
    koala = source.read_bytes()
    if len(koala) != 10003 or koala[:2] != bytes((0x00, 0x60)):
        raise ValueError("expected a standard 10003-byte Koala file loaded at $6000")

    bitmap = bytearray(koala[2:8002])
    screen = koala[8002:9002]
    color_ram = bytearray(koala[9002:10002])
    background = koala[10002]
    font = font_path.read_bytes()
    if len(font) != 36 * 32:
        raise ValueError(f"expected 1152 font bytes, received {len(font)}")
    draw_font16(bitmap, color_ram, font, "A", 19, 0, 5)
    draw_font16(bitmap, color_ram, font, "GAME", 16, 23, 5)
    packed_bitmap = pack(bitmap)
    packed_screen = pack(screen)
    packed_color = pack(color_ram)

    output.mkdir(parents=True, exist_ok=True)
    (output / "presents_bitmap_packed.bin").write_bytes(packed_bitmap)
    (output / "presents_screen_packed.bin").write_bytes(packed_screen)
    (output / "presents_color_packed.bin").write_bytes(packed_color)
    (output / "presents_background.bin").write_bytes(bytes((background,)))
    preview = render_preview(bitmap, screen, color_ram, background)
    with (output / "presents_preview.ppm").open("wb") as file:
        file.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        file.write(preview)

    packed_size = len(packed_bitmap) + len(packed_screen) + len(packed_color)
    print(f"Packed native Koala screen from 10000 to {packed_size} bytes")


if __name__ == "__main__":
    main()
