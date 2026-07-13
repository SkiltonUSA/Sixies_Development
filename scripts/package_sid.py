#!/usr/bin/env python3
"""Wrap the assembled 40-second C64 tune in a PSID v2 header."""

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parent.parent
PRG_PATH = ROOT / "build" / "star-wars-40s.prg"
SID_PATH = ROOT / "build" / "star-wars-40s.sid"


def psid_text(value: str) -> bytes:
    encoded = value.encode("latin-1")[:31]
    return encoded + bytes(32 - len(encoded))


def main() -> None:
    prg = PRG_PATH.read_bytes()
    if prg[:2] != b"\x01\x08":
        raise SystemExit(f"unexpected load address in {PRG_PATH}")

    header = bytearray()
    header += b"PSID"
    header += struct.pack(
        ">HHHHHHHI",
        2,       # version
        0x007C,  # data offset
        0,       # use the PRG's two-byte load address
        0x1000,  # init
        0x1080,  # play
        1,       # songs
        1,       # start song
        0,       # vertical-blank timing
    )
    header += psid_text("Star Wars - C64 Soundtrack 40s")
    header += psid_text("John Williams / C64 arrangement")
    header += psid_text("Original SID arrangement 2026")
    header += struct.pack(">HBBBB", 0x0014, 0, 0, 0, 0)  # PAL, MOS6581

    if len(header) != 0x7C:
        raise AssertionError(f"invalid PSID header size: {len(header)}")

    SID_PATH.write_bytes(header + prg)
    print(f"Built {SID_PATH.relative_to(ROOT)} ({SID_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
