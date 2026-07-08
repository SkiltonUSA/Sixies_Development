#!/usr/bin/env python3
"""Build the original demo SID asset from ACME source."""

from pathlib import Path
import struct
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/music/original_dirge_sid.a"
PRG = ROOT / "build/original_dirge_sid.prg"
OUT = ROOT / "src/assets/sid.psid"


def psid_text(value: str) -> bytes:
    encoded = value.encode("ascii")
    return encoded[:32].ljust(32, b"\0")


def main() -> None:
    (ROOT / "build").mkdir(exist_ok=True)
    subprocess.run(["acme", str(SOURCE)], cwd=ROOT, check=True)

    prg = PRG.read_bytes()
    if prg[:2] != b"\x00\x10":
        raise SystemExit(f"Unexpected SID PRG load address in {PRG}")

    header = bytearray(0x7C)
    header[0:4] = b"PSID"
    struct.pack_into(">HHHHHHHI", header, 4, 2, 0x7C, 0, 0x1000, 0x1003, 1, 1, 0)
    header[0x16:0x36] = psid_text("No More Continues Dirge")
    header[0x36:0x56] = psid_text("Original C64U")
    header[0x56:0x76] = psid_text("2026")

    OUT.write_bytes(bytes(header) + prg)
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
