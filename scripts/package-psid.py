#!/usr/bin/env python3
"""Wrap a raw C64 music payload in a PSID v2 header."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def field(value: str) -> bytes:
    encoded = value.encode("latin-1")[:31]
    return encoded + bytes(32 - len(encoded))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--load", type=lambda value: int(value, 0), default=0x1000)
    parser.add_argument("--init", type=lambda value: int(value, 0), default=0x1000)
    parser.add_argument("--play", type=lambda value: int(value, 0), default=0x1003)
    parser.add_argument("--title", default="Sixies - Rhythmic Grammar")
    parser.add_argument("--author", default="DSkilton")
    parser.add_argument("--released", default="2026")
    args = parser.parse_args()

    header = bytearray()
    header += b"PSID"
    header += struct.pack(">HHHHHHHI", 2, 0x7C, args.load, args.init, args.play, 1, 1, 0)
    header += field(args.title)
    header += field(args.author)
    header += field(args.released)
    header += struct.pack(">HBBBB", 0x14, 0, 0, 0, 0)
    if len(header) != 0x7C:
        raise RuntimeError(f"invalid PSID header size: {len(header)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(header + args.payload.read_bytes())


if __name__ == "__main__":
    main()
