#!/usr/bin/env python3
"""Wrap the assembled music drivers in PSID v2 headers."""

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parent.parent

TUNES = [
    {
        "prg": "better-off-alone-markov.prg",
        "sid": "better-off-alone-markov.sid",
        "name": "Better Off Alone - Markov Loop",
        "author": "MP3 to MIDI to SID",
        "released": "137 BPM PAL loop",
    },
    {
        "prg": "galway-nights.prg",
        "sid": "galway-nights.sid",
        "name": "Galway Nights",
        "author": "Claude (Martin Galway style)",
        "released": "2026 original, 107 BPM PAL loop",
    },
    {
        "prg": "dark-armada.prg",
        "sid": "dark-armada.sid",
        "name": "Dark Armada",
        "author": "SkiltonUSA / Markov generator",
        "released": "2026 original motif-Markov march",
    },
    {
        "prg": "gearshift-markov.prg",
        "sid": "gearshift-markov.sid",
        "name": "Gearshift",
        "author": "SkiltonUSA / Markov generator",
        "released": "2026 original punchy C64 game cue",
    },
]


def psid_text(value: str) -> bytes:
    encoded = value.encode("latin-1")[:31]
    return encoded + bytes(32 - len(encoded))


def package(tune: dict) -> None:
    prg_path = ROOT / "build" / tune["prg"]
    sid_path = ROOT / "build" / tune["sid"]
    prg = prg_path.read_bytes()
    if prg[:2] != b"\x01\x08":
        raise SystemExit(f"unexpected load address in {prg_path}")

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
    header += psid_text(tune["name"])
    header += psid_text(tune["author"])
    header += psid_text(tune["released"])
    header += struct.pack(">HBBBB", 0x0014, 0, 0, 0, 0)  # PAL, MOS6581

    if len(header) != 0x7C:
        raise AssertionError(f"invalid PSID header size: {len(header)}")

    sid_path.write_bytes(header + prg)
    print(f"Built {sid_path.relative_to(ROOT)} ({sid_path.stat().st_size} bytes)")


def main() -> None:
    for tune in TUNES:
        package(tune)


if __name__ == "__main__":
    main()
