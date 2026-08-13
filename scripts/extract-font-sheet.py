#!/usr/bin/env python3

"""Reproduce the Sixies display alphabet as C64 character data.

The reference sheet draws every glyph as a flat colored body wrapped in a white
outline. Only the body carries the letterform, so the sheet is reduced to a
body-only mask and resampled onto the character grid at two sizes:

  * 16x16, a 2x2 block of characters, keeps the rounded bowls, the heavy stems
    and the tiny counters, and is the faithful cut.
  * 8x8, a single character, is the body-text cut. A third of the glyphs turn
    ambiguous once the cap height is only seven pixels, so those are hand drawn;
    the rest are resampled.

Two details matter for fidelity. The white outline anti-aliases through the same
gray that D, J, P, V, 2 and 8 are filled with, so gray candidates are opened to
discard the one-pixel fringe that would otherwise fatten every glyph. And plain
area-coverage thresholding closes the counters of A, B, D, P, R, 4, 6, 8 and 9,
so each enclosed region in the source is reopened after thresholding.
"""

import pathlib
import subprocess
import sys


SHEET_WIDTH = 1536
SHEET_HEIGHT = 1024
TITLE_BAND_BOTTOM = 250
ROW_NAMES = ("ABCDEFGHI", "JKLMNOPQR", "STUVWXYZ", "123456789")
NAMES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

GRAY_LOW, GRAY_HIGH = 48, 96
GRAY_OPEN_RADIUS = 2
SEPARATOR_INK = 900

CELL16, CAP16, BASE16 = 16, 14, 14
CELL8, CAP8, BASE8 = 8, 7, 7
THRESHOLD = 0.5
DESCENDER_RATIO = 0.05

# The charset is indexed by character code, so a full 256-entry table would
# spend 2048 bytes to carry 37 glyphs. Only $20 (space) through $5F is ever
# drawn -- the widest character in use is ']' in the settings pager -- so the
# table starts at $20 and the glyph lookup subtracts that first.
CHARSET_FIRST = 0x20
CHARSET_COUNT = 64

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

# Seven rows of cap height are not enough for the blobby M and W middles, the
# curled C and G terminals, the K arms, or the counters of A and 4: resampling
# collapses them into slabs that read as the wrong letter. Round glyphs also
# land a column off-axis at this size. These follow the reference silhouette by
# hand; every other glyph is resampled.
OVERRIDES_8X8 = {
    "A": ("..###...", ".#####..", ".##.##..", "##...##.",
          "#######.", "##...##.", "##...##.", "........"),
    "C": ("..####..", ".######.", "###..##.", "###.....",
          "###..##.", ".######.", "..####..", "........"),
    "E": (".#####..", ".#####..", ".##.....", ".####...",
          ".##.....", ".#####..", ".#####..", "........"),
    "G": ("..####..", ".######.", "###.....", "###.###.",
          "###..##.", ".######.", "..####..", "........"),
    "K": (".##..##.", ".##.##..", ".####...", ".###....",
          ".####...", ".##.##..", ".##..##.", "........"),
    "M": ("##...##.", "###.###.", "#######.", "##.#.##.",
          "##...##.", "##...##.", "##...##.", "........"),
    "O": ("..####..", ".######.", ".##..##.", ".##..##.",
          ".##..##.", ".######.", "..####..", "........"),
    "R": (".#####..", ".######.", ".##..##.", ".#####..",
          ".#####..", ".##.##..", ".##..##.", "........"),
    "V": (".##..##.", ".##..##.", ".##..##.", ".######.",
          ".######.", "..####..", "...##...", "........"),
    "W": ("##...##.", "##...##.", "##.#.##.", "##.#.##.",
          "#######.", "#######.", ".##.##..", "........"),
    "X": ("##...##.", "##...##.", ".##.##..", "..###...",
          ".##.##..", "##...##.", "##...##.", "........"),
    "0": ("..####..", ".######.", ".##..##.", ".##..##.",
          ".##..##.", ".######.", "..####..", "........"),
    "2": (".#####..", ".######.", "....##..", "..###...",
          ".###....", ".######.", ".######.", "........"),
    "4": ("...##...", "..###...", ".##.##..", "##..##..",
          "#######.", "....##..", "....##..", "........"),
    "9": ("..####..", ".##..##.", ".##..##.", "..#####.",
          "....##..", "...###..", "..###...", "........"),
}

# The reference sheet carries no punctuation. The merge exclamations need an
# exclamation mark, drawn to match the weight of the resampled glyphs. These
# reach the ASCII-indexed charset only; the 8x8 ASM table stays A-Z and 0-9.
EXTRA_8X8 = {
    "!": ("..###...", "..###...", "..###...", "..###...",
          "..###...", "........", "..###...", "........"),
}


def raw_rgb(path):
    return subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])


def open_mask(mask, radius):
    """Erode then dilate, dropping features thinner than the structuring element."""
    height = len(mask)
    width = len(mask[0])
    span = range(-radius, radius + 1)
    kernel = [(dy, dx) for dy in span for dx in span if dy * dy + dx * dx <= radius * radius]
    eroded = [bytearray(width) for _ in range(height)]
    for y in range(radius, height - radius):
        row = mask[y]
        target = eroded[y]
        for x in range(radius, width - radius):
            if row[x] and all(mask[y + dy][x + dx] for dy, dx in kernel):
                target[x] = 1
    opened = [bytearray(width) for _ in range(height)]
    for y in range(radius, height - radius):
        row = eroded[y]
        for x in range(radius, width - radius):
            if not row[x]:
                continue
            for dy, dx in kernel:
                opened[y + dy][x + dx] = 1
    return opened


def body_mask(rgb):
    """Mark glyph-body pixels, excluding the white outline and the paper."""
    colored = [bytearray(SHEET_WIDTH) for _ in range(SHEET_HEIGHT)]
    gray = [bytearray(SHEET_WIDTH) for _ in range(SHEET_HEIGHT)]
    offset = 0
    for y in range(SHEET_HEIGHT):
        colored_row = colored[y]
        gray_row = gray[y]
        for x in range(SHEET_WIDTH):
            red, green, blue = rgb[offset], rgb[offset + 1], rgb[offset + 2]
            offset += 3
            high = max(red, green, blue)
            spread = high - min(red, green, blue)
            if spread > 50 and high > 70:
                colored_row[x] = 1
            elif spread <= 40 and GRAY_LOW <= high <= GRAY_HIGH:
                gray_row[x] = 1
    gray = open_mask(gray, GRAY_OPEN_RADIUS)
    for y in range(SHEET_HEIGHT):
        colored_row = colored[y]
        gray_row = gray[y]
        for x in range(SHEET_WIDTH):
            if gray_row[x]:
                colored_row[x] = 1
    return colored


def runs(flags, minimum):
    found = []
    start = None
    for index, present in enumerate(list(flags) + [False]):
        if present and start is None:
            start = index
        elif not present and start is not None:
            if index - start >= minimum:
                found.append([start, index])
            start = None
    return found


def modal(values):
    return max(set(values), key=values.count)


class Glyph:
    """A body mask plus the cap line and baseline shared by its alphabet row."""

    def __init__(self, rows, cap_top, baseline):
        self.rows = rows
        self.cap_top = cap_top
        self.baseline = baseline
        self.height = len(rows)
        self.width = len(rows[0])


def segment(mask):
    glyphs = {}
    row_has_ink = [any(row) for row in mask]
    for y, row in enumerate(mask):
        if sum(row) > SEPARATOR_INK:
            row_has_ink[y] = False
    bands = [band for band in runs(row_has_ink, 40) if band[0] > TITLE_BAND_BOTTOM]
    if len(bands) != len(ROW_NAMES):
        raise ValueError(f"expected {len(ROW_NAMES)} alphabet rows, found {len(bands)}")

    for (top, bottom), names in zip(bands, ROW_NAMES):
        band = mask[top:bottom]
        column_has_ink = [any(row[x] for row in band) for x in range(SHEET_WIDTH)]
        columns = []
        for start, end in runs(column_has_ink, 8):
            if columns and start - columns[-1][1] <= 14:
                columns[-1][1] = end
            else:
                columns.append([start, end])
        if len(columns) != len(names):
            raise ValueError(f"found {len(columns)} glyphs in row {names}, expected {len(names)}")

        bodies = []
        for start, end in columns:
            cropped = [bytearray(row[start:end]) for row in band]
            inked = [y for y, row in enumerate(cropped) if any(row)]
            left = min(x for row in cropped for x in range(len(row)) if row[x])
            right = max(x for row in cropped for x in range(len(row)) if row[x]) + 1
            bodies.append(([bytearray(row[left:right]) for row in cropped],
                           inked[0], inked[-1] + 1))
        cap_top = modal([top for _, top, _ in bodies])
        baseline = modal([bottom for _, _, bottom in bodies])
        for name, (rows, _, _) in zip(names, bodies):
            glyphs[name] = Glyph(rows, cap_top, baseline)

    glyphs["0"] = glyphs["O"]
    return glyphs


def coverage(glyph, region, cell, cap, base):
    """Fraction of each cell covered by region, on a grid snapped to the glyph edge."""
    scale = (glyph.baseline - glyph.cap_top) / float(cap)
    origin = int((cell - glyph.width / scale) / 2.0)
    result = [[0.0] * cell for _ in range(cell)]
    for ty in range(cell):
        top = glyph.cap_top + (ty - (base - cap)) * scale
        y0 = max(int(top // 1), 0)
        y1 = min(int(-((-(top + scale)) // 1)), glyph.height)
        if y1 <= y0:
            continue
        for tx in range(cell):
            left = (tx - origin) * scale
            x0 = max(int(left // 1), 0)
            x1 = min(int(-((-(left + scale)) // 1)), glyph.width)
            if x1 <= x0:
                continue
            total = sum(sum(region[y][x0:x1]) for y in range(y0, y1))
            result[ty][tx] = total / float((y1 - y0) * (x1 - x0))
    return result


def counters(glyph):
    """Background regions fully enclosed by the body, i.e. the letter counters."""
    seen = [bytearray(glyph.width) for _ in range(glyph.height)]
    found = []
    for sy in range(glyph.height):
        for sx in range(glyph.width):
            if glyph.rows[sy][sx] or seen[sy][sx]:
                continue
            seen[sy][sx] = 1
            pixels = [(sy, sx)]
            pending = [(sy, sx)]
            enclosed = True
            while pending:
                y, x = pending.pop()
                if y in (0, glyph.height - 1) or x in (0, glyph.width - 1):
                    enclosed = False
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < glyph.height and 0 <= nx < glyph.width \
                            and not glyph.rows[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = 1
                        pixels.append((ny, nx))
                        pending.append((ny, nx))
            if enclosed and len(pixels) > 25:
                found.append(pixels)
    return found


def descends(glyph):
    """True when the glyph really drops below the baseline rather than just overshooting.

    Only Q has a tail; the round glyphs clear the baseline by a single source
    pixel, which would otherwise claim the cell's line gap.
    """
    bottom = max(y for y in range(glyph.height) if any(glyph.rows[y])) + 1
    return (bottom - glyph.baseline) > DESCENDER_RATIO * (glyph.baseline - glyph.cap_top)


def render(glyph, cell, cap, base, threshold=THRESHOLD):
    """Resample the body onto one cell, keeping every source counter open."""
    body = coverage(glyph, glyph.rows, cell, cap, base)
    bitmap = [[value >= threshold for value in row] for row in body]
    if not descends(glyph):
        for y in range(base, cell):
            bitmap[y] = [False] * cell
    for pixels in counters(glyph):
        region = [bytearray(glyph.width) for _ in range(glyph.height)]
        for y, x in pixels:
            region[y][x] = 1
        hole = coverage(glyph, region, cell, cap, base)
        peak = max(max(row) for row in hole)
        if peak <= 0.0:
            continue
        limit = max(threshold, peak * 0.75)
        cleared = False
        for y in range(cell):
            for x in range(cell):
                if hole[y][x] >= limit:
                    bitmap[y][x] = False
                    cleared = True
        if not cleared:
            _, best_y, best_x = max((hole[y][x], y, x)
                                    for y in range(cell) for x in range(cell))
            bitmap[best_y][best_x] = False
    return recenter(bitmap, cell)


def recenter(bitmap, cell):
    """Balance the side bearings.

    Sub-pixel sampling leaves a glyph a column left or right of centre depending
    on where its edges land, which reads as uneven spacing once the glyphs sit in
    fixed cells. Centring the thresholded result keeps the whole alphabet aligned.
    """
    inked = [x for row in bitmap for x in range(cell) if row[x]]
    if not inked:
        return bitmap
    shift = (cell - (max(inked) - min(inked) + 1)) // 2 - min(inked)
    if shift == 0:
        return bitmap
    moved = [[False] * cell for _ in range(cell)]
    for y, row in enumerate(bitmap):
        for x in range(cell):
            if row[x]:
                moved[y][x + shift] = True
    return moved


def drawn(pattern):
    return [[column == "#" for column in row] for row in pattern]


def pack_row(row):
    """Pack one bitmap row into bytes, most significant bit leftmost."""
    packed = []
    for start in range(0, len(row), 8):
        value = 0
        for bit in row[start:start + 8]:
            value = (value << 1) | int(bit)
        packed.append(value)
    return packed


def write_font_asm(bitmaps, path):
    lines = [
        "// Sixies font reproduced from SixiesFont_sheet.png",
        "// 8x8 monochrome glyphs, A-Z and 0-9",
        "// Bit 7 = leftmost pixel, Bit 0 = rightmost pixel",
        "",
        "SixiesFont:",
    ]
    for name in NAMES:
        values = ",".join(f"${pack_row(row)[0]:02X}" for row in bitmaps[name])
        lines.extend((f"// {name}", f".byte {values}"))
    lines.extend(("", "SixiesFontEnd:", ".const SIXIES_GLYPH_COUNT = 36",
                  ".const SIXIES_GLYPH_BYTES = 8"))
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_charset(bitmaps, path):
    charset = bytearray(CHARSET_COUNT * 8)
    glyphs = dict(bitmaps)
    glyphs.update({name: drawn(pattern) for name, pattern in EXTRA_8X8.items()})
    for name, bitmap in glyphs.items():
        index = ord(name) - CHARSET_FIRST
        if not 0 <= index < CHARSET_COUNT:
            raise ValueError(f"glyph {name!r} falls outside the charset window")
        charset[index * 8:(index + 1) * 8] = bytes(pack_row(row)[0] for row in bitmap)
    path.write_bytes(charset)


def write_font16(bitmaps, path):
    """Row-interleaved 16x16 glyphs: left byte then right byte, top row first."""
    data = bytearray()
    for name in NAMES:
        for row in bitmaps[name]:
            data.extend(pack_row(row))
    path.write_bytes(data)


def write_digits16(bitmaps, path):
    """16x16 digits in VIC-II character order: top-left, top-right, then the bottom pair."""
    data = bytearray()
    for name in "0123456789":
        packed = [pack_row(row) for row in bitmaps[name]]
        for half in (packed[:8], packed[8:]):
            data.extend(row[0] for row in half)
            data.extend(row[1] for row in half)
    path.write_bytes(data)


def write_colors(path):
    lines = [
        "; Colors sampled from SixiesFont_sheet.png.",
        "SixiesFontColors:",
        "!byte " + ",".join(str(GLYPH_COLORS[name]) for name in NAMES),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_preview(bitmaps, path, cell, names=NAMES, columns=9, scale=4):
    pitch = (cell + 1) * scale
    width = columns * pitch
    height = ((len(names) + columns - 1) // columns) * pitch
    preview = bytearray(width * height * 3)
    for index, name in enumerate(names):
        color = bytes(C64_PALETTE[GLYPH_COLORS[name]])
        origin_x = (index % columns) * pitch
        origin_y = (index // columns) * pitch
        for y, row in enumerate(bitmaps[name]):
            for x, on in enumerate(row):
                if not on:
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        pixel = ((origin_y + y * scale + dy) * width
                                 + origin_x + x * scale + dx) * 3
                        preview[pixel:pixel + 3] = color
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
    if len(rgb) != SHEET_WIDTH * SHEET_HEIGHT * 3:
        raise ValueError(f"font sheet must be {SHEET_WIDTH}x{SHEET_HEIGHT}")
    glyphs = segment(body_mask(rgb))

    large = {name: render(glyphs[name], CELL16, CAP16, BASE16) for name in NAMES}
    small = {
        name: drawn(OVERRIDES_8X8[name]) if name in OVERRIDES_8X8
        else render(glyphs[name], CELL8, CAP8, BASE8)
        for name in NAMES
    }

    write_font_asm(small, output / "SixiesFont_image.asm")
    write_charset(small, output / "SixiesFont_charset.bin")
    write_font16(large, output / "SixiesFont16.bin")
    write_digits16(large, output / "SixiesDigits16.bin")
    write_colors(output / "SixiesFont_colors.asm")
    write_preview(small, output / "SixiesFont_preview.ppm", CELL8)
    write_preview(large, output / "SixiesFont16_preview.ppm", CELL16, scale=2)
    write_preview(large, output / "SixiesDigits16_preview.ppm", CELL16,
                  names="0123456789", columns=5)
    print(f"Reproduced {len(NAMES)} Sixies glyphs at 16x16 and 8x8 "
          f"({len(OVERRIDES_8X8)} hand drawn at 8x8)")


if __name__ == "__main__":
    main()
