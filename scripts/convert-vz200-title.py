#!/usr/bin/env python3
"""Convert the Sixies title master into a compact VZ200 one-bit bitmap."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


WIDTH = 112
HEIGHT = 45
ROW_BYTES = WIDTH // 8
FRAME_WIDTH_BYTES = WIDTH // 4
FRAME_BYTES = FRAME_WIDTH_BYTES * HEIGHT
FILTER = "crop=1500:600:43:170,scale=112:45:flags=neighbor,format=rgb24"


def parse_ppm(path: Path) -> bytes:
    magic, dimensions, maximum, pixels = path.read_bytes().split(b"\n", 3)
    if magic != b"P6" or dimensions != b"112 45" or maximum != b"255":
        raise ValueError(f"unexpected PPM header in {path}")
    expected_length = WIDTH * HEIGHT * 3
    if len(pixels) != expected_length:
        raise ValueError(f"expected {expected_length} image bytes, got {len(pixels)}")
    return pixels


def vz_color(red: int, green: int, blue: int) -> int:
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    if maximum < 48:
        return 0
    if maximum - minimum < 48:
        return 1
    if red >= green and red >= blue:
        if blue > green * 1.15:
            return 2
        return 3
    if blue >= red and blue >= green and red > green * 1.15:
        return 2
    return 1


def pack_frame(pixels: bytes) -> bytes:
    frame = bytearray()
    for row in range(HEIGHT):
        for byte_column in range(FRAME_WIDTH_BYTES):
            packed = 0
            for pixel in range(4):
                x = byte_column * 4 + pixel
                offset = (row * WIDTH + x) * 3
                color = vz_color(*pixels[offset : offset + 3])
                packed |= color << (6 - pixel * 2)
            frame.append(packed)
    return bytes(frame)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SystemExit("ffmpeg is required to generate the VZ200 title bitmap")

    with tempfile.TemporaryDirectory() as directory:
        frame_path = Path(directory) / "title.ppm"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(args.source),
                "-vf",
                FILTER,
                "-frames:v",
                "1",
                "-f",
                "image2",
                "-vcodec",
                "ppm",
                str(frame_path),
            ],
            check=True,
        )
        frame = pack_frame(parse_ppm(frame_path))

    rows = [
        "; Generated from ports/vz200/assets/title-master.png. Do not edit.",
        f"TITLE_FRAME_BYTES EQU {FRAME_BYTES}",
        "TitleFrame:",
    ]
    for row in range(HEIGHT):
        start = row * FRAME_WIDTH_BYTES
        values = ",".join(
            f"${value:02X}" for value in frame[start : start + FRAME_WIDTH_BYTES]
        )
        rows.append(f"        DB      {values}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
