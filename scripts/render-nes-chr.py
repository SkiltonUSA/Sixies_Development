#!/usr/bin/env python3
"""Render raw NES CHR data or CHR ROM from an iNES file to a PNG."""

import argparse
from pathlib import Path

from nes_graphics import (
    indexed_preview,
    parse_ines,
    parse_palette,
    render_chr_sheet,
    render_tilemap,
    write_png,
)


def positive(value):
    result = int(value, 0)
    if result <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Render NES 2bpp CHR data using a four-color palette."
    )
    parser.add_argument("input", type=Path, help="raw CHR or iNES ROM")
    parser.add_argument("output", type=Path, help="output PNG")
    parser.add_argument("--ines", action="store_true",
                        help="read CHR ROM from an iNES file")
    parser.add_argument("--palette", type=parse_palette, default=parse_palette("0f,00,10,20"),
                        help="four NES hex colors (default: 0f,00,10,20)")
    parser.add_argument("--columns", type=positive, default=16,
                        help="tile sheet columns (default: 16)")
    parser.add_argument("--max-tiles", type=positive,
                        help="render only the first N tiles")
    parser.add_argument("--nametable", type=Path,
                        help="render this compact nametable instead of a tile sheet")
    parser.add_argument("--tile-columns", type=positive)
    parser.add_argument("--tile-rows", type=positive)
    args = parser.parse_args()

    try:
        data = args.input.read_bytes()
        chr_data = parse_ines(data).chr_rom if args.ines else data
        if args.nametable:
            if args.tile_columns is None or args.tile_rows is None:
                raise ValueError("--nametable requires --tile-columns and --tile-rows")
            indexed = render_tilemap(
                chr_data,
                args.nametable.read_bytes(),
                args.tile_columns,
                args.tile_rows,
            )
        else:
            if args.tile_columns is not None or args.tile_rows is not None:
                raise ValueError("tile dimensions require --nametable")
            indexed = render_chr_sheet(chr_data, args.columns, args.max_tiles)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_png(args.output, indexed_preview(indexed, args.palette))
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
