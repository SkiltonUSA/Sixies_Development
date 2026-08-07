#!/usr/bin/env python3

import pathlib
import subprocess
import sys


GLYPH_ROWS = (
    ("ABCDEFGHI", ((60, 225), (225, 390), (390, 550), (550, 710), (710, 870),
                   (870, 1030), (1030, 1180), (1180, 1350), (1350, 1470)), (235, 400)),
    ("JKLMNOPQR", ((55, 205), (205, 370), (370, 515), (515, 695), (695, 850),
                   (850, 1015), (1015, 1170), (1170, 1335), (1335, 1480)), (400, 555)),
    ("STUVWXYZ", ((95, 245), (245, 410), (410, 565), (565, 720),
                  (720, 925), (925, 1090), (1090, 1245), (1245, 1415)), (550, 700)),
    ("0123456789", ((90, 230), (230, 325), (325, 460), (460, 595), (595, 730),
                    (730, 860), (860, 995), (995, 1135), (1135, 1280),
                    (1280, 1425)), (720, 870)),
)

GLYPH_COLORS = {
    **dict(zip("ABCDEFGHI", (7, 4, 5, 11, 8, 2, 7, 4, 5))),
    **dict(zip("JKLMNOPQR", (11, 8, 2, 7, 4, 5, 11, 8, 2))),
    **dict(zip("STUVWXYZ", (7, 4, 5, 11, 8, 2, 7, 4))),
    **dict(zip("0123456789", (5, 5, 11, 8, 2, 7, 4, 5, 11, 8))),
}

C64_PALETTE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
]


def raw_rgb(path):
    return subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])


def is_fill(red, green, blue, allow_gray):
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    spread = maximum - minimum
    if spread > 20 and maximum > 32:
        return True
    return allow_gray and spread < 24 and 38 < maximum < 112


def largest_connected_region(points):
    remaining = set(points)
    largest = set()
    while remaining:
        start = remaining.pop()
        region = {start}
        pending = [start]
        while pending:
            x, y = pending.pop()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    region.add(neighbor)
                    pending.append(neighbor)
        if len(region) > len(largest):
            largest = region
    return largest


def extract_mask(rgb, width, x_bounds, y_bounds, allow_gray):
    left, right = x_bounds
    top, bottom = y_bounds
    points = []
    for y in range(top, bottom):
        for x in range(left, right):
            offset = (y * width + x) * 3
            if is_fill(*rgb[offset:offset + 3], allow_gray):
                points.append((x, y))
    if not points:
        raise ValueError(f"no colored glyph pixels in {x_bounds}, {y_bounds}")
    if allow_gray:
        # Gray outline pixels match the numeral fill by color. The fill is the
        # largest region and is separated from the outline by a black gutter.
        points = largest_connected_region(points)
    mask_left = min(x for x, _ in points)
    mask_right = max(x for x, _ in points) + 1
    mask_top = min(y for _, y in points)
    mask_bottom = max(y for _, y in points) + 1
    mask = set(points)
    return mask, (mask_left, mask_top, mask_right - mask_left, mask_bottom - mask_top)


def reduce_glyph(mask, bounds):
    left, top, source_width, source_height = bounds
    scale = min(8 / source_width, 8 / source_height)
    target_width = max(1, round(source_width * scale))
    target_height = max(1, round(source_height * scale))
    target_left = (8 - target_width) // 2
    target_top = (8 - target_height) // 2
    rows = []
    for output_y in range(8):
        row = 0
        for output_x in range(8):
            local_x = output_x - target_left
            local_y = output_y - target_top
            on = False
            if 0 <= local_x < target_width and 0 <= local_y < target_height:
                source_x = left + ((local_x * 2 + 1) * source_width) // (target_width * 2)
                source_y = top + ((local_y * 2 + 1) * source_height) // (target_height * 2)
                on = (source_x, source_y) in mask
            row = (row << 1) | int(on)
        rows.append(row)
    return bytes(rows)


def reduce_digit(mask, bounds):
    left, top, source_width, source_height = bounds
    scale = min(15 / source_width, 15 / source_height)
    target_width = max(1, round(source_width * scale))
    target_height = max(1, round(source_height * scale))
    target_left = (16 - target_width) // 2
    target_top = (16 - target_height) // 2
    rows = []
    for output_y in range(16):
        row = 0
        for output_x in range(16):
            local_x = output_x - target_left
            local_y = output_y - target_top
            on = False
            if 0 <= local_x < target_width and 0 <= local_y < target_height:
                source_x = left + ((local_x * 2 + 1) * source_width) // (target_width * 2)
                source_y = top + ((local_y * 2 + 1) * source_height) // (target_height * 2)
                on = (source_x, source_y) in mask
            row = (row << 1) | int(on)
        rows.append(row)
    return rows


def extract_glyphs(rgb, width):
    glyphs = {}
    digits = {}
    for names, columns, rows in GLYPH_ROWS:
        for name, column in zip(names, columns):
            extracted = extract_mask(rgb, width, column, rows, GLYPH_COLORS[name] == 11)
            glyphs[name] = reduce_glyph(*extracted)
            if name.isdigit():
                digits[name] = reduce_digit(*extracted)
    return glyphs, digits


def write_asm(glyphs, path):
    lines = [
        "// Sixies font extracted from SixiesFont_sheet.png",
        "// 8x8 monochrome glyphs, A-Z and 0-9",
        "// Bit 7 = leftmost pixel, Bit 0 = rightmost pixel",
        "",
        "SixiesFont:",
    ]
    for name in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        values = ",".join(f"${value:02X}" for value in glyphs[name])
        lines.extend((f"// {name}", f".byte {values}"))
    lines.extend(("", "SixiesFontEnd:", ".const SIXIES_GLYPH_COUNT = 36", ".const SIXIES_GLYPH_BYTES = 8"))
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_charset(glyphs, path):
    charset = bytearray(2048)
    for name, glyph in glyphs.items():
        code = ord(name)
        charset[code * 8:(code + 1) * 8] = glyph
    path.write_bytes(charset)


def write_colors(path):
    values = [GLYPH_COLORS[name] for name in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"]
    lines = [
        "; Colors sampled from SixiesFont_sheet.png.",
        "SixiesFontColors:",
        "!byte " + ",".join(str(value) for value in values),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def digit_character_order(rows):
    top = rows[:8]
    bottom = rows[8:]
    return bytes(
        [row >> 8 for row in top]
        + [row & 0xff for row in top]
        + [row >> 8 for row in bottom]
        + [row & 0xff for row in bottom]
    )


def write_digits(digits, path):
    path.write_bytes(b"".join(digit_character_order(digits[name]) for name in "0123456789"))


def write_digit_preview(digits, path):
    scale = 4
    cell = 17 * scale
    width = 5 * cell
    height = 2 * cell
    preview = bytearray(width * height * 3)
    for index, name in enumerate("0123456789"):
        origin_x = (index % 5) * cell
        origin_y = (index // 5) * cell
        color = C64_PALETTE[GLYPH_COLORS[name]]
        for y, row in enumerate(digits[name]):
            for x in range(16):
                if not row & (1 << (15 - x)):
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        pixel = ((origin_y + y * scale + dy) * width + origin_x + x * scale + dx) * 3
                        preview[pixel:pixel + 3] = bytes(color)
    with path.open("wb") as file:
        file.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        file.write(preview)


def write_preview(glyphs, path):
    scale = 4
    cell = 9 * scale
    columns = 9
    names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    width = columns * cell
    height = 4 * cell
    preview = bytearray(width * height * 3)
    for index, name in enumerate(names):
        origin_x = (index % columns) * cell
        origin_y = (index // columns) * cell
        color = C64_PALETTE[GLYPH_COLORS[name]]
        for y, row in enumerate(glyphs[name]):
            for x in range(8):
                if not row & (1 << (7 - x)):
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        pixel = ((origin_y + y * scale + dy) * width + origin_x + x * scale + dx) * 3
                        preview[pixel:pixel + 3] = bytes(color)
    with path.open("wb") as file:
        file.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        file.write(preview)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract-font-sheet.py FONT_SHEET.png OUTPUT_DIRECTORY")
    source = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    rgb = raw_rgb(source)
    if len(rgb) != 1536 * 1024 * 3:
        raise ValueError("font sheet must be 1536x1024")
    glyphs, digits = extract_glyphs(rgb, 1536)
    write_asm(glyphs, output / "SixiesFont_image.asm")
    write_charset(glyphs, output / "SixiesFont_charset.bin")
    write_colors(output / "SixiesFont_colors.asm")
    write_preview(glyphs, output / "SixiesFont_preview.ppm")
    write_digits(digits, output / "SixiesDigits16.bin")
    write_digit_preview(digits, output / "SixiesDigits16_preview.ppm")
    print("Extracted A-Z and 0-9 from the supplied font sheet")


if __name__ == "__main__":
    main()
