#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


ENTRY_COUNT = 10
ENTRY_BYTES = 5
DATA_OFFSET = 6
FILE_BYTES = DATA_OFFSET + ENTRY_COUNT * ENTRY_BYTES
MAGIC = b"SIXH"
VERSION = 1
DEFAULT_ENTRIES = (
    (b"DOM", 1349),
    (b"PRI", 1020),
    (b"TWD", 893),
    (b"TAN", 802),
    (b"TB ", 755),
)


def build_table() -> bytes:
    table = bytearray(FILE_BYTES)
    table[:4] = MAGIC
    table[4] = VERSION
    for index in range(ENTRY_COUNT):
        offset = DATA_OFFSET + index * ENTRY_BYTES
        table[offset : offset + 3] = b"---"
    for index, (initials, score) in enumerate(DEFAULT_ENTRIES):
        offset = DATA_OFFSET + index * ENTRY_BYTES
        table[offset : offset + 3] = initials
        table[offset + 3] = score & 0xFF
        table[offset + 4] = score >> 8
    table[5] = sum(table[DATA_OFFSET:]) & 0xFF
    return bytes(table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the seeded SIXIES high-score table")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build_table())


if __name__ == "__main__":
    main()
