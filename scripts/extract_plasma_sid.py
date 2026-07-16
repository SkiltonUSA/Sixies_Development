#!/usr/bin/env python3
"""Extract the native-load payload used by the plasma-scene SID player."""

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "music" / "pat_and_mat_vs_starwars.sid"
OUTPUT = ROOT / "src" / "generated" / "plasma_starwars_sid.bin"

EXPECTED_INIT = 0x1000
EXPECTED_PLAY = 0x1003
STAGING_ADDRESS = 0xD000
STAGING_LIMIT = 0xDC00


def main() -> None:
    data = SOURCE.read_bytes()
    if len(data) < 0x7C or data[:4] != b"PSID":
        raise ValueError("expected a PSID file with a complete v2 header")

    version, data_offset, load, init, play, songs, start = struct.unpack(
        ">7H", data[4:18]
    )
    if version < 2 or data_offset < 0x7C:
        raise ValueError(f"unsupported PSID version/data offset: {version}/{data_offset}")
    if songs != 1 or start != 1:
        raise ValueError(f"expected one song starting at 1, got {songs}/{start}")

    payload = data[data_offset:]
    if load == 0:
        if len(payload) < 2:
            raise ValueError("PSID payload is missing its embedded load address")
        load = payload[0] | payload[1] << 8
        payload = payload[2:]

    if (load, init, play) != (EXPECTED_INIT, EXPECTED_INIT, EXPECTED_PLAY):
        raise ValueError(
            f"unexpected load/init/play: ${load:04x}/${init:04x}/${play:04x}"
        )
    if STAGING_ADDRESS + len(payload) > STAGING_LIMIT:
        raise ValueError(
            f"{len(payload)}-byte SID payload exceeds RAM beneath I/O"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(payload)
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} ({len(payload)} bytes, "
        f"${load:04x}-${load + len(payload) - 1:04x})"
    )


if __name__ == "__main__":
    main()
