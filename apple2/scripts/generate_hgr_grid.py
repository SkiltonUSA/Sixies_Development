#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


WIDTH = 280
HEIGHT = 160
PAGE_BYTES = 8192
BOARD_BITMAP_LEFT = 6
BOARD_BITMAP_TOP = 6
BOARD_BITMAP_SIZE = 141
TILE_WIDTH_BYTES = 5
TILE_HEIGHT = 28
TILE_BYTES = TILE_WIDTH_BYTES * TILE_HEIGHT
TILES_BYTES = 25 * TILE_BYTES

BOARD_SIZE = 5
CELL_SIZE = 24
CELL_GAP = 4
BOARD_LEFT = 8
BOARD_TOP = 8
SIDEBAR_LEFT = 176
SIDEBAR_TOP = 16

FONT = {
    "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"),
    "I": ("111", "010", "010", "010", "111"),
    "M": ("101", "111", "111", "101", "101"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "S": ("111", "100", "111", "001", "111"),
    "T": ("111", "010", "010", "010", "010"),
    "X": ("101", "101", "010", "101", "101"),
}


def row_offset(y: int) -> int:
    return ((y & 7) << 10) + (((y >> 3) & 7) << 7) + ((y >> 6) * 40)


class Canvas:
    def __init__(self) -> None:
        self.pixels = bytearray(WIDTH * HEIGHT)

    def pixel(self, x: int, y: int) -> None:
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            self.pixels[y * WIDTH + x] = 1

    def hline(self, x1: int, x2: int, y: int, dotted: bool = False) -> None:
        for x in range(x1, x2 + 1):
            if not dotted or ((x - x1) & 3) < 2:
                self.pixel(x, y)

    def vline(self, x: int, y1: int, y2: int, dotted: bool = False) -> None:
        for y in range(y1, y2 + 1):
            if not dotted or ((y - y1) & 3) < 2:
                self.pixel(x, y)

    def rect(self, x: int, y: int, width: int, height: int) -> None:
        self.hline(x, x + width - 1, y)
        self.hline(x, x + width - 1, y + height - 1)
        self.vline(x, y, y + height - 1)
        self.vline(x + width - 1, y, y + height - 1)

    def double_rect(self, x: int, y: int, width: int, height: int) -> None:
        self.rect(x, y, width, height)
        self.rect(x + 1, y + 1, width - 2, height - 2)

    def label(self, x: int, y: int, text: str, scale: int = 1) -> None:
        cursor = x
        for character in text:
            glyph = FONT[character]
            for row, bits in enumerate(glyph):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        for offset_y in range(scale):
                            for offset_x in range(scale):
                                self.pixel(
                                    cursor + column * scale + offset_x,
                                    y + row * scale + offset_y,
                                )
            cursor += 4 * scale


def draw_corner_brackets(canvas: Canvas) -> None:
    canvas.hline(2, 5, 4)
    canvas.vline(2, 4, 18)
    canvas.hline(146, 149, 4)
    canvas.vline(149, 4, 18)
    canvas.hline(2, 5, 151)
    canvas.vline(2, 137, 151)
    canvas.hline(146, 149, 151)
    canvas.vline(149, 137, 151)


def draw_grid(canvas: Canvas) -> None:
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            x = BOARD_LEFT + column * (CELL_SIZE + CELL_GAP)
            y = BOARD_TOP + row * (CELL_SIZE + CELL_GAP)
            canvas.double_rect(x, y, CELL_SIZE, CELL_SIZE)


def draw_master_grid(canvas: Canvas, master_path: Path) -> None:
    with Image.open(master_path) as source:
        grayscale = source.convert("L")
    content = grayscale.point(lambda value: 255 if value >= 64 else 0)
    bounds = content.getbbox()
    if bounds is None:
        raise ValueError(f"grid master has no visible pixels: {master_path}")

    resized = grayscale.crop(bounds).resize(
        (BOARD_BITMAP_SIZE, BOARD_BITMAP_SIZE),
        Image.Resampling.LANCZOS,
    )
    for y in range(BOARD_BITMAP_SIZE):
        for x in range(BOARD_BITMAP_SIZE):
            if resized.getpixel((x, y)) >= 96:
                canvas.pixel(BOARD_BITMAP_LEFT + x, BOARD_BITMAP_TOP + y)


def draw_sidebar(canvas: Canvas) -> None:
    panel_x = SIDEBAR_LEFT - 6
    panel_y = SIDEBAR_TOP - 6
    canvas.double_rect(panel_x, panel_y, 92, 78)
    canvas.label(panel_x + 9, panel_y + 2, "NEXT", scale=2)
    canvas.hline(panel_x + 8, panel_x + 83, panel_y + 13, dotted=True)

    mode_y = SIDEBAR_TOP + 82
    canvas.double_rect(panel_x, mode_y, 92, 52)
    canvas.label(panel_x + 9, mode_y + 5, "MODE")
    canvas.hline(panel_x + 8, panel_x + 83, mode_y + 12, dotted=True)
    canvas.double_rect(SIDEBAR_LEFT + 8, SIDEBAR_TOP + 92, 52, 24)

    canvas.vline(panel_x - 4, panel_y + 6, panel_y + 70, dotted=True)
    canvas.vline(panel_x + 95, panel_y + 6, panel_y + 70, dotted=True)


def draw_footer(canvas: Canvas) -> None:
    canvas.hline(8, 148, 153, dotted=True)
    canvas.hline(8, 224, 156, dotted=True)
    canvas.label(236, 153, "SIXIES")
    canvas.hline(262, 271, 156)
    canvas.hline(268, 271, 153)


def build_canvas(master_path: Path | None = None) -> Canvas:
    canvas = Canvas()
    if master_path is None:
        draw_corner_brackets(canvas)
        draw_grid(canvas)
    else:
        draw_master_grid(canvas, master_path)
    draw_sidebar(canvas)
    draw_footer(canvas)
    return canvas


def pack_hgr(canvas: Canvas) -> bytearray:
    page = bytearray(PAGE_BYTES)
    for y in range(HEIGHT):
        base = row_offset(y)
        for x in range(WIDTH):
            if canvas.pixels[y * WIDTH + x]:
                page[base + x // 7] |= 1 << (x % 7)
    return page


def pack_grid_tiles(page: bytearray) -> bytearray:
    tiles = bytearray()
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            byte_offset = column * 4
            y = BOARD_BITMAP_TOP + row * TILE_HEIGHT
            for line in range(TILE_HEIGHT):
                address = row_offset(y + line) + byte_offset
                tiles.extend(page[address : address + TILE_WIDTH_BYTES])
    if len(tiles) != TILES_BYTES:
        raise AssertionError(f"unexpected grid tile size: {len(tiles)}")
    return tiles


def save_preview(canvas: Canvas, path: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), (5, 11, 14))
    image.putdata([
        (236, 232, 204) if pixel else (5, 11, 14)
        for pixel in canvas.pixels
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    image.resize((WIDTH * 4, HEIGHT * 4), Image.Resampling.NEAREST).save(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the SIXIES HGR grid background")
    parser.add_argument("--input", required=True, type=Path, help="source grid artwork")
    parser.add_argument("--output", required=True, type=Path, help="8 KB HGR page output")
    parser.add_argument("--tiles", required=True, type=Path, help="packed dirty-tile backgrounds")
    parser.add_argument("--preview", required=True, type=Path, help="PNG preview output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    canvas = build_canvas(args.input)
    page = pack_hgr(canvas)
    tiles = pack_grid_tiles(page)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(page)
    args.tiles.write_bytes(tiles)
    save_preview(canvas, args.preview)


if __name__ == "__main__":
    main()
