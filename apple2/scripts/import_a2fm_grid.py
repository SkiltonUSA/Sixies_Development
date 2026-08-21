#!/usr/bin/env python3
"""Import and validate the full-screen A2FM gameplay grid."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).parent
IMPORT_SPEC = importlib.util.spec_from_file_location(
    "import_a2fm_asset", SCRIPT_DIR / "import_a2fm_asset.py"
)
assert IMPORT_SPEC is not None and IMPORT_SPEC.loader is not None
A2FM = importlib.util.module_from_spec(IMPORT_SPEC)
IMPORT_SPEC.loader.exec_module(A2FM)

WIDTH = 280
HEIGHT = 192
VISIBLE_HEIGHT = 160
PAGE_BYTES = 8192
BOARD_SIZE = 5
CELL_SIZE = 24
CELL_PITCH_X = 29
CELL_PITCH_Y = 30
BOARD_LEFT = 69
BOARD_TOP = 8
DIE_LEFTS = (70, 98, 128, 158, 186)
DIE_TOPS = (8, 38, 68, 99, 129)
SIDEBAR_CLEAR_BOX = (458, 7, 544, 143)
SIDEBAR_LABELS = (("CUR", 459, 15), ("NEXT", 459, 75))
SCORE_LABEL_CLEAR_BOX = (32, 34, 77, 40)
SCORE_LABEL = ("TOTAL", 36, 35)
SCORE_CLEAR_BOX = (24, 43, 89, 54)
MASCOT_CLEAR_BOX = (13, 52, 100, 143)
MASCOT_BOX = (13, 59, 88, 55)

FONT = {
    "A": ("010", "101", "111", "101", "101"),
    "C": ("111", "100", "100", "100", "111"),
    "E": ("111", "100", "110", "100", "111"),
    "L": ("100", "100", "100", "100", "111"),
    "N": ("101", "111", "111", "111", "101"),
    "O": ("111", "101", "101", "101", "111"),
    "R": ("110", "101", "110", "101", "101"),
    "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"),
    "X": ("101", "101", "010", "101", "101"),
}


def hgr_offset(y: int) -> int:
    return ((y & 0x07) << 10) + (((y >> 3) & 0x07) << 7) + (y >> 6) * 0x28


def collapse_to_hgr(source: Image.Image) -> Image.Image:
    if source.size != (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT):
        raise ValueError("decoded A2FM grid must be 560x192")

    output = Image.new("L", (WIDTH, HEIGHT), 0)
    source_pixels = source.load()
    output_pixels = output.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if source_pixels[x * 2, y] or source_pixels[x * 2 + 1, y]:
                output_pixels[x, y] = 255
    return output


def pack_hgr(image: Image.Image) -> bytearray:
    if image.size != (WIDTH, HEIGHT):
        raise ValueError("HGR grid must be 280x192")

    page = bytearray(PAGE_BYTES)
    pixels = image.load()
    for y in range(HEIGHT):
        row = hgr_offset(y)
        for x in range(WIDTH):
            if pixels[x, y] >= 128:
                page[row + x // 7] |= 1 << (x % 7)
    return page


def draw_label(
    image: Image.Image,
    text: str,
    x: int,
    y: int,
    scale_x: int = 2,
    scale_y: int | None = None,
) -> None:
    if scale_y is None:
        scale_y = scale_x
    pixels = image.load()
    cursor = x
    for character in text:
        for row, bits in enumerate(FONT[character]):
            for column, bit in enumerate(bits):
                if bit == "0":
                    continue
                for offset_y in range(scale_y):
                    for offset_x in range(scale_x):
                        pixels[
                            cursor + column * scale_x + offset_x,
                            y + row * scale_y + offset_y,
                        ] = 255
        cursor += 4 * scale_x


def draw_mascot(image: Image.Image, mascot_path: Path) -> None:
    with Image.open(mascot_path) as source:
        grayscale = source.convert("L")
    content = grayscale.point(lambda value: 255 if value >= 32 else 0)
    bounds = content.getbbox()
    if bounds is None:
        raise ValueError(f"mascot has no visible pixels: {mascot_path}")

    left, top, width, height = MASCOT_BOX
    resized = grayscale.crop(bounds).resize((width, height), Image.Resampling.LANCZOS)
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            if resized.getpixel((x, y)) >= 48:
                pixels[left + x, top + y] = 255


def build_runtime_grid(
    main: bytes,
    auxiliary: bytes,
    mascot_path: Path,
) -> tuple[bytes, bytes, Image.Image]:
    image = A2FM.decode_mono(main, auxiliary)
    pixels = image.load()
    left, top, right, bottom = SIDEBAR_CLEAR_BOX
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            pixels[x, y] = 0
    for text, x, y in SIDEBAR_LABELS:
        draw_label(image, text, x, y)
    left, top, right, bottom = SCORE_LABEL_CLEAR_BOX
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            pixels[x, y] = 0
    text, x, y = SCORE_LABEL
    draw_label(image, text, x, y, scale_x=2, scale_y=1)
    left, top, right, bottom = SCORE_CLEAR_BOX
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            pixels[x, y] = 0
    left, top, right, bottom = MASCOT_CLEAR_BOX
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            pixels[x, y] = 0
    draw_mascot(image, mascot_path)

    runtime_main = bytearray(PAGE_BYTES)
    runtime_auxiliary = bytearray(PAGE_BYTES)
    for y in range(HEIGHT):
        row = hgr_offset(y)
        for signal in range(A2FM.SCREEN_WIDTH):
            if pixels[signal, y] < 128:
                continue
            sequence_byte = signal // 7
            bank = runtime_auxiliary if sequence_byte & 1 == 0 else runtime_main
            bank[row + sequence_byte // 2] |= 1 << (signal % 7)
    return bytes(runtime_main), bytes(runtime_auxiliary), image


def validate_black_cell_interiors(main: bytes, auxiliary: bytes) -> None:
    if len(main) != PAGE_BYTES or len(auxiliary) != PAGE_BYTES:
        raise ValueError("A2FM grid banks must each be exactly 8192 bytes")

    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            left = DIE_LEFTS[column] * 2
            top = DIE_TOPS[row]
            for line in range(CELL_SIZE):
                row_address = hgr_offset(top + line)
                for signal in range(left, left + CELL_SIZE * 2):
                    sequence_byte = signal // 7
                    bank = auxiliary if sequence_byte & 1 == 0 else main
                    if bank[row_address + sequence_byte // 2] & (1 << (signal % 7)):
                        raise ValueError(
                            f"grid cell ({column},{row}) interior is not black at signal {signal}"
                        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import the SIXIES A2FM gameplay screen")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--mascot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    main_page, auxiliary_page = A2FM.split_a2fm(args.input.read_bytes())
    decoded = A2FM.decode_mono(main_page, auxiliary_page)
    with Image.open(args.reference) as reference:
        expected = decoded.resize(
            (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT * 2),
            Image.Resampling.NEAREST,
        )
        if reference.size != expected.size:
            raise ValueError("grid reference must be 560x384")
        if A2FM.monochrome_bytes(reference) != expected.tobytes():
            raise ValueError("decoded grid A2FM does not match the reference PNG")

    runtime_main, runtime_auxiliary, decoded = build_runtime_grid(
        main_page,
        auxiliary_page,
        args.mascot,
    )
    validate_black_cell_interiors(runtime_main, runtime_auxiliary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(runtime_auxiliary + runtime_main)
    decoded.resize(
        (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT * 2),
        Image.Resampling.NEAREST,
    ).save(args.preview)


if __name__ == "__main__":
    main()
