#!/usr/bin/env python3
"""Convert the high-score mascot master to a transparent VZ200 overlay."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


WIDTH = 38
HEIGHT = 30
FILTER = "crop=1080:850:160:150,scale=38:30:flags=neighbor,format=rgb24"


def parse_ppm(path: Path) -> bytes:
    magic, dimensions, maximum, pixels = path.read_bytes().split(b"\n", 3)
    if magic != b"P6" or dimensions != b"38 30" or maximum != b"255":
        raise ValueError(f"unexpected PPM header in {path}")
    if len(pixels) != WIDTH * HEIGHT * 3:
        raise ValueError(f"unexpected PPM data length in {path}")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required to generate the VZ200 mascot")

    with tempfile.TemporaryDirectory() as directory:
        image_path = Path(directory) / "mascot.ppm"
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(args.source),
                "-vf", FILTER, "-frames:v", "1", "-f", "image2", "-vcodec", "ppm",
                str(image_path),
            ],
            check=True,
        )
        pixels = parse_ppm(image_path)

    rows = [
        "; Generated from ports/vz200/assets/high-score-mascot-master.png. Do not edit.",
        "HighScoreMascot:",
    ]
    for row in range(HEIGHT):
        values = []
        for column in range(WIDTH):
            offset = (row * WIDTH + column) * 3
            values.append(f"${vz_color(*pixels[offset : offset + 3]):02X}")
        rows.append("        DB      " + ",".join(values))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
