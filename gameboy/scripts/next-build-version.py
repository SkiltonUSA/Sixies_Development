#!/usr/bin/env python3
"""Advance Sixies' persistent build number and write its C header."""

from argparse import ArgumentParser
from pathlib import Path


MAX_VERSION = 4_294_967_295


def main():
    parser = ArgumentParser()
    parser.add_argument("--counter", type=Path, required=True)
    parser.add_argument("--header", type=Path, required=True)
    args = parser.parse_args()

    try:
        current = int(args.counter.read_text().strip())
    except (FileNotFoundError, ValueError):
        current = 0

    if current < 0 or current >= MAX_VERSION:
        raise SystemExit("Sixies build version is outside the supported range")

    version = current + 1
    args.counter.write_text(f"{version}\n")
    args.header.write_text(
        "#ifndef SIXIES_BUILD_VERSION_H\n"
        "#define SIXIES_BUILD_VERSION_H\n\n"
        f"#define SIXIES_BUILD_VERSION {version}UL\n\n"
        "#endif\n"
    )
    print(f"Sixies build version V.{version:03d}")


if __name__ == "__main__":
    main()
