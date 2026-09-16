#!/usr/bin/env python3
"""Create a versioned Sixies ROM artifact matching the title-screen version."""

from argparse import ArgumentParser
from pathlib import Path
import shutil


def main():
    parser = ArgumentParser()
    parser.add_argument("--counter", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    args = parser.parse_args()

    version = int(args.counter.read_text().strip())
    archive = args.rom.with_name(f"sixies-V.{version:03d}.gb")
    shutil.copy2(args.rom, archive)
    print(f"Versioned ROM: {archive.name}")


if __name__ == "__main__":
    main()
