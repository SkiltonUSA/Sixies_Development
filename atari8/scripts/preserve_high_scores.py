#!/usr/bin/env python3
"""Seed or preserve Sixies' raw high-score sector in a 90K ATR image."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


ATR_HEADER_BYTES = 16
SECTOR_BYTES = 128
HIGH_SCORE_SECTOR = 720
HIGH_SCORE_BYTES = 56
MAGIC = b"SIXH"
VERSION = 1
DEFAULT_ENTRIES = (
    (b"DOM", 1349),
    (b"PRI", 1020),
    (b"TWD", 893),
    (b"TAN", 802),
    (b"TB ", 755),
    (b"ACE", 650),
    (b"MAX", 540),
    (b"ZED", 430),
    (b"BOT", 320),
    (b"CPU", 210),
)


def sector_offset(sector: int = HIGH_SCORE_SECTOR) -> int:
    return ATR_HEADER_BYTES + (sector - 1) * SECTOR_BYTES


def default_table() -> bytes:
    data = bytearray(HIGH_SCORE_BYTES)
    data[:4] = MAGIC
    data[4] = VERSION
    for index, (initials, score) in enumerate(DEFAULT_ENTRIES):
        offset = 6 + index * 5
        data[offset : offset + 3] = initials
        data[offset + 3] = score & 0xFF
        data[offset + 4] = score >> 8
    data[5] = sum(data[6:]) & 0xFF
    return bytes(data)


def valid_table(data: bytes) -> bool:
    if len(data) < HIGH_SCORE_BYTES:
        return False
    table = data[:HIGH_SCORE_BYTES]
    if table[:4] != MAGIC or table[4] != VERSION:
        return False
    if table[5] != sum(table[6:]) & 0xFF:
        return False
    previous = 0xFFFF
    for index in range(10):
        offset = 6 + index * 5
        initials = table[offset : offset + 3]
        if any(value != 0x20 and not 0x41 <= value <= 0x5A for value in initials):
            return False
        score = table[offset + 3] | table[offset + 4] << 8
        if score > previous:
            return False
        previous = score
    return True


def read_table(path: Path) -> bytes | None:
    if not path.is_file():
        return None
    image = path.read_bytes()
    offset = sector_offset()
    table = image[offset : offset + HIGH_SCORE_BYTES]
    return table if valid_table(table) else None


def install_table(new_image: Path, output: Path, table: bytes) -> None:
    image = bytearray(new_image.read_bytes())
    offset = sector_offset()
    if len(image) < offset + SECTOR_BYTES:
        raise ValueError("ATR image does not contain sector 720")
    image[offset : offset + SECTOR_BYTES] = bytes(SECTOR_BYTES)
    image[offset : offset + HIGH_SCORE_BYTES] = table
    new_image.write_bytes(image)
    os.replace(new_image, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    table = read_table(args.old) or default_table()
    install_table(args.new, args.output, table)


if __name__ == "__main__":
    main()
