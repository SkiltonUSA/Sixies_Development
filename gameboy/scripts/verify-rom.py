#!/usr/bin/env python3

import argparse
from pathlib import Path


NINTENDO_LOGO = bytes.fromhex(
    "CEED6666CC0D000B03730083000C000D"
    "0008111F8889000E DCCC6EE6DDDDD999"
    "BBBB67636E0EECCC DDDC999FBBB9333E".replace(" ", "")
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a built Game Boy ROM header.")
    parser.add_argument("rom", type=Path)
    return parser.parse_args()


def header_checksum(data: bytes) -> int:
    checksum = 0
    for value in data[0x134:0x14D]:
        checksum = (checksum - value - 1) & 0xFF
    return checksum


def global_checksum(data: bytes) -> int:
    return (sum(data) - data[0x14E] - data[0x14F]) & 0xFFFF


def main() -> None:
    args = parse_args()
    data = args.rom.read_bytes()
    errors = []

    if len(data) < 0x150 or len(data) % 0x4000 != 0:
        errors.append(f"unexpected ROM size: {len(data)} bytes")
    if data[0x104:0x134] != NINTENDO_LOGO:
        errors.append("Nintendo logo is invalid")

    title = data[0x134:0x143].rstrip(b"\0").decode("ascii", errors="replace")
    if title != "SIXIES":
        errors.append(f"unexpected title: {title!r}")
    if data[0x143] != 0x80:
        errors.append(f"expected DMG/GBC compatibility flag 0x80, got 0x{data[0x143]:02X}")
    if data[0x147] != 0x1B:
        errors.append(f"expected MBC5+RAM+BATTERY type 0x1B, got 0x{data[0x147]:02X}")
    if data[0x149] != 0x02:
        errors.append(f"expected 8 KiB SRAM code 0x02, got 0x{data[0x149]:02X}")
    if data[0x14A] != 0x01:
        errors.append(f"expected non-Japanese region 0x01, got 0x{data[0x14A]:02X}")
    if data[0x14D] != header_checksum(data):
        errors.append("header checksum is invalid")

    expected_global = (data[0x14E] << 8) | data[0x14F]
    if expected_global != global_checksum(data):
        errors.append("global checksum is invalid")

    if errors:
        raise SystemExit("ROM verification failed:\n  " + "\n  ".join(errors))

    print(
        f"Verified {args.rom}: {title}, {len(data) // 1024} KiB, "
        "DMG/GBC, MBC5+8 KiB SRAM+battery"
    )


if __name__ == "__main__":
    main()
