#!/usr/bin/env python3
"""Convert the Death Star banner PNG to hires bitmap data for the intro.

The demo's bitmap convention is background = 1-bits, ink = 0-bits, so the
logo bytes can be AND-merged over the starfield. Output covers the full
320x80 area above the crawl, plus one screen colour byte per 8x8 cell.
"""

from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
PNG_PATH = ROOT / "src" / "assets" / "deathstar_logo.png"
OUT_PATH = ROOT / "src" / "generated" / "logo.inc"

SCREEN_WIDTH = 320
CHAR_ROWS = 10
LOGO_HEIGHT = CHAR_ROWS * 8
BAYER_4X4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)

# C64 palette entries used for per-cell foreground colours.
C64_COLORS = {
    (255, 255, 255): 1,   # white
    (104, 55, 152): 4,    # purple
    (88, 141, 67): 5,     # green
    (53, 40, 121): 6,     # blue
    (80, 80, 80): 11,     # dark grey
    (120, 120, 120): 12,  # grey
    (108, 94, 181): 14,   # light blue
    (159, 159, 159): 15,  # light grey
}


def decode_png(path: Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"not a PNG: {path}")
    pos, idat, width, height, color_type = 8, b"", 0, 0, 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if kind == b"IHDR":
            width, height, depth, color_type = struct.unpack(
                ">IIBB", data[pos + 8:pos + 18])
            if depth != 8 or color_type not in (2, 6):
                raise SystemExit("expected 8-bit RGB or RGBA PNG")
        elif kind == b"IDAT":
            idat += data[pos + 8:pos + 8 + length]
        pos += 12 + length

    raw = zlib.decompress(idat)
    bpp = 4 if color_type == 6 else 3
    stride = width * bpp
    rows, prev, p = [], bytearray(stride), 0
    for _ in range(height):
        filt = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if filt == 1:
                line[i] = (line[i] + a) & 255
            elif filt == 2:
                line[i] = (line[i] + b) & 255
            elif filt == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif filt == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 255
        if bpp == 3:
            rgba = bytearray(width * 4)
            for x in range(width):
                rgba[x * 4:x * 4 + 4] = line[x * 3:x * 3 + 3] + b"\xff"
            rows.append(bytes(rgba))
        else:
            rows.append(bytes(line))
        prev = line
    return width, height, rows


def luminance(rgb):
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def display_tone(rgb):
    # Lift contrast before dithering: black space stays empty, mid greys turn
    # into halftone texture, and bright highlights remain mostly solid.
    return max(0, min(255, (luminance(rgb) - 8) * 1.28))


def nearest_c64(rgb):
    best = min(C64_COLORS, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, rgb)))
    return C64_COLORS[best]


def content_bbox(width: int, height: int, rows):
    row_counts = [0] * height
    col_counts = [0] * width
    for y in range(height):
        row = rows[y]
        for x in range(width):
            r, g, b, a = row[x * 4:x * 4 + 4]
            if a > 128 and luminance((r, g, b)) > 24:
                row_counts[y] += 1
                col_counts[x] += 1

    row_threshold = max(80, width // 24)
    col_threshold = max(60, height // 18)
    ys = [index for index, count in enumerate(row_counts)
          if count >= row_threshold]
    xs = [index for index, count in enumerate(col_counts)
          if count >= col_threshold]
    if not xs or not ys:
        raise SystemExit("logo image contains no visible pixels")
    pad_x = max(8, (max(xs) - min(xs)) // 40)
    pad_y = max(8, (max(ys) - min(ys)) // 40)
    return (
        max(0, min(xs) - pad_x),
        max(0, min(ys) - pad_y),
        min(width, max(xs) + pad_x + 1),
        min(height, max(ys) + pad_y + 1),
    )


def sample_area(rows, x0: float, y0: float, x1: float, y1: float):
    ix0, iy0 = int(x0), int(y0)
    ix1, iy1 = max(ix0 + 1, int(x1 + 0.999)), max(iy0 + 1, int(y1 + 0.999))
    total = [0, 0, 0, 0]
    count = 0
    for y in range(iy0, iy1):
        row = rows[y]
        for x in range(ix0, ix1):
            r, g, b, a = row[x * 4:x * 4 + 4]
            total[0] += r
            total[1] += g
            total[2] += b
            total[3] += a
            count += 1
    return tuple(value // count for value in total)


def main() -> None:
    width, height, rows = decode_png(PNG_PATH)
    left, top, right, bottom = content_bbox(width, height, rows)
    crop_width = right - left
    crop_height = bottom - top

    pixels = [[(0, 0, 0, 0)] * SCREEN_WIDTH for _ in range(LOGO_HEIGHT)]
    for y in range(LOGO_HEIGHT):
        sy0 = top + y * crop_height / LOGO_HEIGHT
        sy1 = top + (y + 1) * crop_height / LOGO_HEIGHT
        for x in range(SCREEN_WIDTH):
            sx0 = left + x * crop_width / SCREEN_WIDTH
            sx1 = left + (x + 1) * crop_width / SCREEN_WIDTH
            pixels[y][x] = sample_area(rows, sx0, sy0, sx1, sy1)

    ink = [[False] * SCREEN_WIDTH for _ in range(LOGO_HEIGHT)]
    cell_rgb = [[[] for _ in range(SCREEN_WIDTH // 8)] for _ in range(CHAR_ROWS)]
    for y in range(LOGO_HEIGHT):
        for x in range(SCREEN_WIDTH):
            r, g, b, a = pixels[y][x]
            threshold = (BAYER_4X4[y & 3][x & 3] + 0.5) * 16
            if a > 128 and display_tone((r, g, b)) > threshold:
                ink[y][x] = True
                cell_rgb[y // 8][x // 8].append((r, g, b))

    # Bitmap: char row r, char column c, line l -> byte r*320 + c*8 + l.
    bitmap = bytearray(CHAR_ROWS * SCREEN_WIDTH)
    for row in range(CHAR_ROWS):
        for col in range(SCREEN_WIDTH // 8):
            for line in range(8):
                byte = 0xFF
                for bit in range(8):
                    if ink[row * 8 + line][col * 8 + bit]:
                        byte &= ~(0x80 >> bit)
                bitmap[row * SCREEN_WIDTH + col * 8 + line] = byte

    colors = []
    for row in range(CHAR_ROWS):
        for col in range(SCREEN_WIDTH // 8):
            samples = cell_rgb[row][col]
            if not samples:
                colors.append(1)
                continue
            avg = tuple(sum(sample[i] for sample in samples) // len(samples)
                        for i in range(3))
            colors.append(nearest_c64(avg))

    lines = ["; Generated by scripts/generate_logo.py.",
             f"LOGO_CHAR_ROWS = {CHAR_ROWS}",
             "logo_bitmap:"]
    for start in range(0, len(bitmap), 16):
        row = ",".join(f"${b:02x}" for b in bitmap[start:start + 16])
        lines.append(f"    !byte {row}")
    lines.append("logo_colors:")
    for start in range(0, len(colors), 16):
        row = ",".join(f"${c:02x}" for c in colors[start:start + 16])
        lines.append(f"    !byte {row}")
    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"Wrote {OUT_PATH.relative_to(ROOT)} ({width}x{height} source, "
          f"crop={crop_width}x{crop_height}@{left},{top}, "
          f"output={SCREEN_WIDTH}x{LOGO_HEIGHT})")


if __name__ == "__main__":
    main()
