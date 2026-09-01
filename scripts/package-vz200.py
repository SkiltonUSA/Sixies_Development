#!/usr/bin/env python3
"""Wrap a sjasmplus binary in VZEM's 24-byte VZF1 autostart format."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_address(value: str) -> int:
    address = int(value, 0)
    if not 0 <= address <= 0xFFFF:
        raise argparse.ArgumentTypeError("address must fit in 16 bits")
    return address


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--load-address", type=parse_address, default=0x7AE9)
    args = parser.parse_args()

    name = args.name.upper().encode("ascii")
    if not 1 <= len(name) <= 8 or not name.isalnum():
        parser.error("--name must contain one to eight ASCII letters or digits")

    payload = args.input.read_bytes()
    header = b"VZF1" + name.ljust(17, b"\0") + bytes((0xF1,))
    header += args.load_address.to_bytes(2, "little")
    assert len(header) == 24

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(header + payload)


if __name__ == "__main__":
    main()
