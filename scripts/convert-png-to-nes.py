#!/usr/bin/env python3
"""Convert a PNG into NES CHR, tilemap, palette, metadata, and preview files."""

import argparse
from pathlib import Path

from nes_graphics import convert_png, parse_palette


def integer(value):
    result = int(value, 0)
    if result < 0:
        raise argparse.ArgumentTypeError("value must not be negative")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Convert PNG artwork to one NES 2bpp background palette and CHR tiles."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output_prefix", type=Path)
    parser.add_argument("--width", type=integer, help="resize width in pixels")
    parser.add_argument("--height", type=integer, help="resize height in pixels")
    parser.add_argument("--palette", type=parse_palette,
                        help="four NES hex colors, for example 0f,00,28,27")
    parser.add_argument("--background", type=lambda value: int(value, 16), default=0x0f,
                        help="automatic palette background color (default: 0f)")
    parser.add_argument("--alpha-threshold", type=integer, default=96)
    parser.add_argument("--dither", action="store_true", help="apply ordered color dithering")
    parser.add_argument("--no-deduplicate", action="store_true")
    parser.add_argument("--tile-limit", type=integer, default=256)
    parser.add_argument("--chr-size", type=integer, default=4096,
                        help="pad CHR to this byte size; use 0 for no padding")
    args = parser.parse_args()

    try:
        paths, metadata = convert_png(
            args.input,
            args.output_prefix,
            width=args.width,
            height=args.height,
            palette=args.palette,
            background=args.background,
            alpha_threshold=args.alpha_threshold,
            dither=args.dither,
            deduplicate=not args.no_deduplicate,
            tile_limit=args.tile_limit,
            chr_size=args.chr_size,
        )
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f"Wrote {paths['chr']} ({metadata['unique_tiles']} unique tiles)")
    print(f"Palette: {','.join(metadata['palette'])}")
    print(f"Preview: {paths['preview']}")


if __name__ == "__main__":
    main()
