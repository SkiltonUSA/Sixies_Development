#!/usr/bin/env python3
"""Split a b2d A2FM file into Apple II DHGR auxiliary and main pages."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


PAGE_BYTES = 8192
SCREEN_WIDTH = 560
SCREEN_HEIGHT = 192


def hgr_offset(y: int) -> int:
    return ((y & 0x07) << 10) + (((y >> 3) & 0x07) << 7) + (y >> 6) * 0x28


def split_a2fm(data: bytes) -> tuple[bytes, bytes]:
    if len(data) != PAGE_BYTES * 2:
        raise ValueError(f"A2FM file must be exactly {PAGE_BYTES * 2} bytes")

    # b2d writes the complete auxiliary page before the complete main page.
    auxiliary = data[:PAGE_BYTES]
    main = data[PAGE_BYTES:]
    return main, auxiliary


def decode_mono(main: bytes, auxiliary: bytes) -> Image.Image:
    if len(main) != PAGE_BYTES or len(auxiliary) != PAGE_BYTES:
        raise ValueError("DHGR banks must each be exactly 8192 bytes")

    image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 0)
    pixels = image.load()
    for y in range(SCREEN_HEIGHT):
        row = hgr_offset(y)
        x = 0
        for byte_index in range(40):
            for bank in (auxiliary, main):
                value = bank[row + byte_index]
                for bit in range(7):
                    pixels[x, y] = 255 if value & (1 << bit) else 0
                    x += 1
    return image


def monochrome_bytes(image: Image.Image) -> bytes:
    return image.convert("L").point(lambda value: 255 if value >= 128 else 0).tobytes()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a b2d DHGR monochrome image")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--aux", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--reference", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    main_page, auxiliary_page = split_a2fm(args.input.read_bytes())
    preview = decode_mono(main_page, auxiliary_page).resize(
        (SCREEN_WIDTH, SCREEN_HEIGHT * 2), Image.Resampling.NEAREST
    )

    if args.reference is not None:
        with Image.open(args.reference) as reference:
            if reference.size != preview.size:
                raise ValueError(
                    f"reference must be {preview.width}x{preview.height}, got "
                    f"{reference.width}x{reference.height}"
                )
            if monochrome_bytes(reference) != preview.tobytes():
                raise ValueError("decoded A2FM image does not match the reference PNG")

    args.main.parent.mkdir(parents=True, exist_ok=True)
    args.aux.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.main.write_bytes(main_page)
    args.aux.write_bytes(auxiliary_page)
    preview.save(args.preview)


if __name__ == "__main__":
    main()
