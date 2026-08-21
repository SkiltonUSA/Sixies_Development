#!/usr/bin/env python3

import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile


APPLESINGLE_MAGIC = 0x00051600
APPLESINGLE_VERSION = 0x00020000
DATA_FORK_ID = 1
PRODOS_INFO_ID = 11
NATIVE_LOAD_ADDRESS = 0x4000
SFX_LOAD_ADDRESS = 0x080D
SFX_BASIC_ADDRESS = 0x0801
SFX_BASIC_STUB = bytes((
    0x0B, 0x08, 0x37, 0x01, 0x8C, 0x32,
    0x30, 0x36, 0x31, 0x00, 0x00, 0x00,
))


def parse_applesingle(data: bytes) -> tuple[bytes, int, int]:
    if len(data) < 26:
        raise ValueError("AppleSingle file is truncated")
    magic, version = struct.unpack_from(">II", data)
    if magic != APPLESINGLE_MAGIC or version != APPLESINGLE_VERSION:
        raise ValueError("input is not an AppleSingle v2 file")

    entry_count = struct.unpack_from(">H", data, 24)[0]
    entries: dict[int, bytes] = {}
    for index in range(entry_count):
        descriptor = 26 + index * 12
        if descriptor + 12 > len(data):
            raise ValueError("AppleSingle entry table is truncated")
        entry_id, offset, length = struct.unpack_from(">III", data, descriptor)
        if offset + length > len(data):
            raise ValueError("AppleSingle entry extends past end of file")
        entries[entry_id] = data[offset:offset + length]

    if DATA_FORK_ID not in entries or PRODOS_INFO_ID not in entries:
        raise ValueError("AppleSingle data fork or ProDOS metadata is missing")
    prodos_info = entries[PRODOS_INFO_ID]
    if len(prodos_info) != 8:
        raise ValueError("invalid ProDOS metadata length")
    _, file_type, aux_type = struct.unpack(">HHI", prodos_info)
    return entries[DATA_FORK_ID], file_type, aux_type


def exomizer_version(exomizer: str) -> str:
    result = subprocess.run(
        (exomizer, "-v"),
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"Exomizer v([0-9.]+)", result.stdout + result.stderr)
    if match is None:
        raise RuntimeError("could not determine Exomizer version")
    return match.group(1)


def crunch(input_path: Path, output_path: Path, exomizer: str) -> None:
    if exomizer_version(exomizer) != "3.1.2":
        raise RuntimeError("SIXIES requires Exomizer 3.1.2")

    native_data, file_type, aux_type = parse_applesingle(input_path.read_bytes())
    if file_type != 0x06 or aux_type != NATIVE_LOAD_ADDRESS:
        raise ValueError("cc65 input must be a ProDOS BIN loaded at $4000")
    native_prg = struct.pack("<H", NATIVE_LOAD_ADDRESS) + native_data

    with tempfile.TemporaryDirectory(prefix="sixies-exomizer-") as temp_name:
        temp_dir = Path(temp_name)
        prg_path = temp_dir / "SIXIES.PRG"
        sfx_path = temp_dir / "SIXIES.SFX"
        restored_path = temp_dir / "SIXIES.RESTORED.PRG"
        prg_path.write_bytes(native_prg)

        subprocess.run(
            (
                exomizer, "sfx", "0x4000", "-t162", "-n", "-q",
                "-o", str(sfx_path), str(prg_path),
            ),
            check=True,
        )
        subprocess.run(
            (exomizer, "desfx", "-q", "-o", str(restored_path), str(sfx_path)),
            check=True,
        )
        if restored_path.read_bytes() != native_prg:
            raise RuntimeError("Exomizer round-trip verification failed")

        sfx_data, sfx_type, sfx_aux_type = parse_applesingle(sfx_path.read_bytes())
        if sfx_type != 0xFC or sfx_aux_type != SFX_BASIC_ADDRESS:
            raise ValueError("Exomizer did not produce the expected Apple II SFX")
        if not sfx_data.startswith(SFX_BASIC_STUB):
            raise ValueError("unexpected Exomizer Apple II BASIC launcher")
        output_path.write_bytes(sfx_data[len(SFX_BASIC_STUB):])

    print(
        f"Exomizer 3.1.2: {len(native_data)} -> {output_path.stat().st_size} bytes "
        f"(ProDOS BIN entry ${SFX_LOAD_ADDRESS:04X})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a verified Exomizer Apple II SFX payload"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--exomizer", default="exomizer")
    args = parser.parse_args()
    crunch(args.input, args.output, args.exomizer)


if __name__ == "__main__":
    main()
