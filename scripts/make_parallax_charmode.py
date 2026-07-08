#!/usr/bin/env python3
"""Convert the repo-local PARALLAX PNG into a vertical hi-res charmode logo.

Outputs:
  parallax_chars.bin  - unique 8x8 hi-res tiles (<=192, placed at char $40)
  parallax_screen.bin - compact screen-code block for the logo
  parallax_color.bin  - compact colour RAM block for the logo

The background stays global via $d021; each hi-res cell gets one foreground
colour via colour RAM, which keeps the logo compatible with the main text mode
screen while preserving as much colour variation per cell as the VIC allows.
"""

from __future__ import annotations

import struct
import sys
import zlib
from collections import Counter

IMG = "src/assets/parallax_logo.png"
NW = int(sys.argv[1]) if len(sys.argv) > 1 else 8
NH = int(sys.argv[2]) if len(sys.argv) > 2 else 20
CHAR_BASE = 0x40
BG = 0x04  # magenta / purple
FLIP_X = True
FLIP_Y = True


def decode_png(path: str) -> tuple[int, int, int, bytearray]:
    data = open(path, "rb").read()
    pos = 8
    width = height = color_type = None
    idat = b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        if chunk_type == b"IHDR":
            width, height = struct.unpack(">II", chunk_data[:8])
            color_type = chunk_data[9]
        elif chunk_type == b"IDAT":
            idat += chunk_data
        elif chunk_type == b"IEND":
            break
        pos += 12 + length

    if width is None or height is None or color_type is None:
        raise ValueError("invalid PNG")

    bpp = 4 if color_type == 6 else 3
    raw = zlib.decompress(idat)
    stride = width * bpp
    image = bytearray()
    prev = bytearray(stride)
    p = 0

    def paeth(a: int, b: int, c: int) -> int:
        pa = abs(b - c)
        pb = abs(a - c)
        pc = abs(a + b - 2 * c)
        if pa <= pb and pa <= pc:
            return a
        if pb <= pc:
            return b
        return c

    for _ in range(height):
        filt = raw[p]
        p += 1
        line = bytearray(raw[p : p + stride])
        p += stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            x = line[i]
            if filt == 0:
                val = x
            elif filt == 1:
                val = x + a
            elif filt == 2:
                val = x + b
            elif filt == 3:
                val = x + ((a + b) >> 1)
            else:
                val = x + paeth(a, b, c)
            line[i] = val & 0xFF
        image += line
        prev = line
    return width, height, bpp, image


WIDTH, HEIGHT, BPP, IMAGE = decode_png(IMG)


def rgb(x: int, y: int) -> tuple[int, int, int]:
    off = (y * WIDTH + x) * BPP
    return IMAGE[off], IMAGE[off + 1], IMAGE[off + 2]


PAL = [
    (0, 0, 0),
    (255, 255, 255),
    (104, 55, 43),
    (112, 164, 178),
    (111, 61, 134),
    (88, 141, 67),
    (53, 40, 121),
    (184, 199, 111),
    (111, 79, 37),
    (67, 57, 0),
    (154, 103, 89),
    (68, 68, 68),
    (108, 108, 108),
    (154, 210, 132),
    (108, 94, 181),
    (149, 149, 149),
]


def nearest_c64(col: tuple[int, int, int]) -> int:
    return min(
        range(16),
        key=lambda i: sum((a - b) ** 2 for a, b in zip(col, PAL[i])),
    )


def rotate_cw(x: int, y: int, src_h: int) -> tuple[int, int]:
    return y, src_h - 1 - x


def crop_bounds() -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = WIDTH, HEIGHT, 0, 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            r, g, b = rgb(x, y)
            if r + g + b > 60:
                x0 = min(x0, x)
                y0 = min(y0, y)
                x1 = max(x1, x)
                y1 = max(y1, y)
    return x0, y0, x1 + 1, y1 + 1


src_x0, src_y0, src_x1, src_y1 = crop_bounds()
crop_w = src_x1 - src_x0
crop_h = src_y1 - src_y0
rot_w = crop_h
rot_h = crop_w
pix_w = NW * 8
pix_h = NH * 8

# Sample the rotated logo into the hi-res grid.
grid: list[list[int | None]] = [[None] * pix_w for _ in range(pix_h)]
for py in range(pix_h):
    for px in range(pix_w):
        if FLIP_X:
            rx0 = (pix_w - (px + 1)) * rot_w // pix_w
            rx1 = max(rx0 + 1, (pix_w - px) * rot_w // pix_w)
        else:
            rx0 = px * rot_w // pix_w
            rx1 = max(rx0 + 1, (px + 1) * rot_w // pix_w)
        if FLIP_Y:
            ry0 = (pix_h - (py + 1)) * rot_h // pix_h
            ry1 = max(ry0 + 1, (pix_h - py) * rot_h // pix_h)
        else:
            ry0 = py * rot_h // pix_h
            ry1 = max(ry0 + 1, (py + 1) * rot_h // pix_h)
        lit = 0
        total = 0
        colors = Counter()
        for ry in range(ry0, ry1):
            for rx in range(rx0, rx1):
                sx, sy = rotate_cw(rx, ry, crop_h)
                sx += src_x0
                sy += src_y0
                r, g, b = rgb(sx, sy)
                total += 1
                if r + g + b > 65:
                    lit += 1
                    colors[nearest_c64((r, g, b))] += 1
        if lit * 2 >= total and colors:
            grid[py][px] = colors.most_common(1)[0][0]


def color_distance(a: int, b: int) -> int:
    return sum((x - y) ** 2 for x, y in zip(PAL[a], PAL[b]))


tiles: dict[tuple[int, ...], int] = {}
order: list[list[int]] = []
screen: list[int] = []
color: list[int] = []

for cy in range(NH):
    for cx in range(NW):
        cell_colors = Counter()
        for ry in range(8):
            for rx in range(8):
                c = grid[cy * 8 + ry][cx * 8 + rx]
                if c is not None:
                    cell_colors[c] += 1
        if not cell_colors:
            screen.append(0x20)
            color.append(0x01)
            continue

        fg = cell_colors.most_common(1)[0][0]
        if fg == BG:
            fg = min((i for i in range(16) if i != BG), key=lambda i: color_distance(i, BG))

        tile_bytes = []
        for ry in range(8):
            byte = 0
            for rx in range(8):
                c = grid[cy * 8 + ry][cx * 8 + rx]
                if c is None:
                    continue
                if color_distance(c, fg) <= color_distance(c, BG):
                    byte |= 0x80 >> rx
            tile_bytes.append(byte)

        key = tuple(tile_bytes)
        if key not in tiles:
            tiles[key] = len(order)
            order.append(tile_bytes)
        screen.append(CHAR_BASE + tiles[key])
        color.append(fg)

if len(order) > 192:
    print(f"unique tiles: {len(order)} exceeds 192 tile budget")
    sys.exit(2)

chars = bytearray()
for tile in order:
    chars += bytes(tile)
chars += bytes((192 - len(order)) * 8)

open("src/assets/parallax_chars.bin", "wb").write(chars)
open("src/assets/parallax_screen.bin", "wb").write(bytes(screen))
open("src/assets/parallax_color.bin", "wb").write(bytes(color))

print(f"wrote {len(order)} unique tiles for {NW}x{NH} vertical hi-res logo")
