#!/usr/bin/env python3
"""Composite vader2 over the full-screen C64 hires ripple plasma scene."""

from pathlib import Path

from generate_logo import decode_png


ROOT = Path(__file__).resolve().parent.parent
VADER_PREVIEW = ROOT / "src" / "assets" / "vader2.png"
VADER_BITMAP = ROOT / "src" / "generated" / "vader2_hires_bitmap.bin"
VADER_SCREEN = ROOT / "src" / "generated" / "vader2_hires_screen.bin"
BITMAP_OUT = ROOT / "src" / "generated" / "pilot_hires_bitmap.bin"
BITMAP_PRG_OUT = ROOT / "src" / "generated" / "pilot_hires_bitmap.prg"
SCREEN_OUT = ROOT / "src" / "generated" / "pilot_hires_screen.bin"
PACKED_OUT = ROOT / "src" / "generated" / "pilot_hires_bitmap.packbits"
RIPPLE_OUT = ROOT / "src" / "generated" / "pilot_ripple_field.bin"
RIPPLE_PRG_OUT = ROOT / "src" / "generated" / "pilot_ripple_field.prg"
PREVIEW_OUT = ROOT / "src" / "generated" / "pilot_hires_preview.ppm"
MESSAGE_TABLES_OUT = ROOT / "src" / "generated" / "plasma_message.inc"

WIDTH = 320
HEIGHT = 200
VADER_SHIFT_CELLS = 11
BLACK = (0, 0, 0)
BLUE = (64, 49, 141)
CIRCLE = bytes((0x00, 0x3c, 0x7e, 0xff, 0xff, 0x7e, 0x3c, 0x00))
BLANK = bytes(8)
TITLE_WORDS = ("RETRODNA", "PRESENTS", "STARWARS")
TITLE_LEFT = 5
TITLE_TOP = 10
TITLE_WIDTH = 31
TITLE_ROWS = 5
FONT_3X5 = {
    "A": ("010", "101", "111", "101", "101"),
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "G": ("111", "100", "101", "101", "111"),
    "H": ("101", "101", "111", "101", "101"),
    "I": ("1", "1", "1", "1", "1"),
    "N": ("101", "111", "111", "101", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "P": ("110", "101", "110", "100", "100"),
    "R": ("110", "101", "110", "101", "101"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"),
}


def packbits(data: bytes) -> bytes:
    output = bytearray()
    index = 0
    while index < len(data):
        run = 1
        while index + run < len(data) and data[index + run] == data[index] and run < 128:
            run += 1
        if run >= 3:
            output.extend((257 - run, data[index]))
            index += run
            continue
        start = index
        index += run
        while index < len(data):
            next_run = 1
            while index + next_run < len(data) and data[index + next_run] == data[index] and next_run < 128:
                next_run += 1
            if next_run >= 3 or index - start + next_run > 128:
                break
            index += next_run
        output.append(index - start - 1)
        output.extend(data[start:index])
    return bytes(output)


def title_frames():
    frames = []
    for word in TITLE_WORDS:
        final_cells = set()
        for character_index, character in enumerate(word):
            glyph = FONT_3X5[character]
            for y, row in enumerate(glyph):
                for x, pixel in enumerate(row):
                    if pixel == "1":
                        final_cells.add((TITLE_TOP + y,
                                         TITLE_LEFT + character_index * 4 + x))
        cells = sorted(final_cells, key=lambda cell: (
            (cell[0] * 73 + cell[1] * 151) & 0xff, cell[0] ^ cell[1]
        ))
        frames.append([
            (row - TITLE_TOP) * TITLE_WIDTH + (col - TITLE_LEFT)
            for row, col in cells
        ])
    return frames


def main() -> None:
    vader_bitmap = VADER_BITMAP.read_bytes()
    vader_screen = VADER_SCREEN.read_bytes()
    vader_width, vader_height, vader_rows = decode_png(VADER_PREVIEW)
    if (vader_width, vader_height, len(vader_bitmap), len(vader_screen)) != (320, 200, 8000, 1000):
        raise SystemExit("vader2 must be a complete 320x200 C64 hires image")

    portrait_cells = [[False] * 40 for _ in range(25)]
    for cell_y in range(25):
        for cell_x in range(40 - VADER_SHIFT_CELLS):
            source_cell_x = cell_x + VADER_SHIFT_CELLS
            portrait_cells[cell_y][cell_x] = any(
                any(vader_rows[cell_y * 8 + y][(source_cell_x * 8 + x) * 4:
                                                  (source_cell_x * 8 + x) * 4 + 3])
                for y in range(8) for x in range(8)
            )
    bitmap = bytearray()
    screen = bytearray(1000)
    for cell_y in range(25):
        for cell_x in range(40):
            if portrait_cells[cell_y][cell_x]:
                source_cell_x = cell_x + VADER_SHIFT_CELLS
                source_offset = cell_y * 320 + source_cell_x * 8
                bitmap.extend(vader_bitmap[source_offset:source_offset + 8])
                screen[cell_y * 40 + cell_x] = vader_screen[cell_y * 40 + source_cell_x]
            else:
                bitmap.extend(CIRCLE if ((cell_y ^ cell_x) & 1) == 0 else BLANK)

    # One packed phase byte per checkerboard circle. $ff marks a cell covered
    # by Vader so the runtime preserves its static hires ink.
    ripple = bytearray()
    centers = ((10.0, 7.0), (30.0, 17.0))
    for row in range(25):
        first_col = 38 + (row & 1)
        for col in range(first_col, -1, -2):
            if portrait_cells[row][col]:
                ripple.append(0xff)
                continue
            phases = [
                int(round(((col - cx) ** 2 + (row - cy) ** 2) ** 0.5 * 2.0)) & 0x0f
                for cx, cy in centers
            ]
            packed_phase = phases[0] | (phases[1] << 4)
            ripple.append(0xef if packed_phase == 0xff else packed_phase)

    packed = packbits(bitmap)
    BITMAP_OUT.write_bytes(bitmap)
    BITMAP_PRG_OUT.write_bytes(bytes((0x00, 0xe0)) + bitmap)
    SCREEN_OUT.write_bytes(screen)
    PACKED_OUT.write_bytes(packed)
    RIPPLE_OUT.write_bytes(ripple)
    RIPPLE_PRG_OUT.write_bytes(bytes((0x00, 0x86)) + ripple)

    def byte_lines(label, values):
        lines = [f"{label}:"]
        for start in range(0, len(values), 16):
            lines.append("    !byte " + ",".join(
                f"${value:02x}" for value in values[start:start + 16]
            ))
        return lines

    frames = title_frames()
    table_lines = [
        "; Generated by scripts/generate_pilot_hires.py.",
        f"PLASMA_TITLE_FRAME_COUNT = {len(frames)}",
        f"PLASMA_TITLE_LEFT = {TITLE_LEFT}",
        f"PLASMA_TITLE_TOP = {TITLE_TOP}",
        f"PLASMA_TITLE_WIDTH = {TITLE_WIDTH}",
        f"PLASMA_TITLE_ROWS = {TITLE_ROWS}",
    ]
    table_lines += byte_lines("plasma_title_frame_lengths", [len(frame) for frame in frames])
    table_lines.append("plasma_title_frame_lo:")
    table_lines.append("    !byte " + ",".join(
        f"<plasma_title_frame_{index}" for index in range(len(frames))
    ))
    table_lines.append("plasma_title_frame_hi:")
    table_lines.append("    !byte " + ",".join(
        f">plasma_title_frame_{index}" for index in range(len(frames))
    ))
    for index, frame in enumerate(frames):
        table_lines += byte_lines(f"plasma_title_frame_{index}", frame)
    table_lines += byte_lines("plasma_bitmap_row_lo", [(0xe000 + row * 320) & 0xff for row in range(25)])
    table_lines += byte_lines("plasma_bitmap_row_hi", [(0xe000 + row * 320) >> 8 for row in range(25)])
    table_lines += byte_lines("plasma_screen_row_lo", [(0xc000 + row * 40) & 0xff for row in range(25)])
    table_lines += byte_lines("plasma_screen_row_hi", [(0xc000 + row * 40) >> 8 for row in range(25)])
    table_lines += byte_lines("plasma_field_row_lo", [(0x8600 + row * 20) & 0xff for row in range(25)])
    table_lines += byte_lines("plasma_field_row_hi", [(0x8600 + row * 20) >> 8 for row in range(25)])
    table_lines += byte_lines("plasma_message_circle", list(CIRCLE))
    MESSAGE_TABLES_OUT.write_text("\n".join(table_lines) + "\n", encoding="ascii")

    with PREVIEW_OUT.open("wb") as preview:
        preview.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        for y in range(HEIGHT):
            line = y & 7
            for x in range(WIDTH):
                cell_x = x // 8
                if portrait_cells[y // 8][cell_x]:
                    source_x = x + VADER_SHIFT_CELLS * 8
                    color = vader_rows[y][source_x * 4:source_x * 4 + 3]
                else:
                    is_circle_cell = ((y // 8 ^ cell_x) & 1) == 0
                    is_set = CIRCLE[line] & (0x80 >> (x & 7))
                    color = BLUE if is_circle_cell and is_set else BLACK
                preview.write(bytes(color))

    print(
        f"Wrote vader2/plasma hires scene: {len(bitmap)} bitmap bytes, "
        f"{len(screen)} screen bytes, {len(ripple)} ripple bytes, "
        f"{len(packed)} PackBits bytes, {len(frames)} title frames"
    )


if __name__ == "__main__":
    main()
