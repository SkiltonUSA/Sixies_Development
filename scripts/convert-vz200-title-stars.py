#!/usr/bin/env python3
"""Convert title-star PNG references to tiny transparent VZ200 overlays."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


SPRITES = (
    ("purple.png", "TitleStarPurple", 20, 20, 2),
    ("green.png", "TitleStarGreen", 20, 20, 1),
    ("gold.png", "TitleStarGold", 20, 20, 1),
    ("spark-orange.png", "TitleSparkOrange", 5, 4, 3),
    ("spark-yellow.png", "TitleSparkYellow", 5, 4, 3),
)


def parse_ppm(path: Path, width: int, height: int) -> bytes:
    magic, dimensions, maximum, pixels = path.read_bytes().split(b"\n", 3)
    if magic != b"P6" or dimensions != f"{width} {height}".encode() or maximum != b"255":
        raise ValueError(f"unexpected PPM header in {path}")
    if len(pixels) != width * height * 3:
        raise ValueError(f"unexpected PPM data length in {path}")
    return pixels


def convert_sprite(source: Path, width: int, height: int, color: int, work: Path) -> bytes:
    output = work / f"{source.stem}.ppm"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-vf", f"scale={width}:{height}:flags=neighbor,format=rgb24",
            "-frames:v", "1", "-f", "image2", "-vcodec", "ppm", str(output),
        ],
        check=True,
    )
    pixels = parse_ppm(output, width, height)
    result = bytearray()
    for offset in range(0, len(pixels), 3):
        red, green, blue = pixels[offset : offset + 3]
        # Near-black is transparent, preserving the static title underneath.
        result.append(color if max(red, green, blue) >= 48 else 0)
    return bytes(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required to generate VZ200 title stars")

    rows = ["; Generated from ports/vz200/assets/title-stars. Do not edit."]
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        for filename, label, width, height, color in SPRITES:
            sprite = convert_sprite(args.source_directory / filename, width, height, color, work)
            rows.append(label + ":")
            for row in range(height):
                values = ",".join(
                    f"${value:02X}" for value in sprite[row * width : (row + 1) * width]
                )
                rows.append(f"        DB      {values}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(rows) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
