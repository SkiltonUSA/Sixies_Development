#!/usr/bin/env python3
"""Convert source art into Apple II double-hi-res main/aux page data."""

from __future__ import annotations

import argparse
import colorsys
from pathlib import Path

from PIL import Image, ImageOps


PAGE_WIDTH = 140
PAGE_HEIGHT = 192
PAGE_BYTES = 8192
VISIBLE_HEIGHT = 160

# Canonical DHGR nibble order. The two grey entries are intentionally distinct
# codes even though they are nearly indistinguishable on an Apple IIe.
DHGR_PALETTE = (
    (0x00, 0x00, 0x00),  # 0 black
    (0x9D, 0x09, 0x66),  # 1 magenta
    (0x2A, 0x2A, 0xE5),  # 2 dark blue
    (0xC7, 0x34, 0xFF),  # 3 purple
    (0x00, 0x71, 0x0A),  # 4 dark green
    (0x6E, 0x6E, 0x6E),  # 5 dark grey
    (0x1B, 0x9A, 0xF3),  # 6 medium blue
    (0xA0, 0xD7, 0xFF),  # 7 light blue
    (0x7B, 0x4B, 0x00),  # 8 brown
    (0xF1, 0x6A, 0x00),  # 9 orange
    (0x99, 0x99, 0x99),  # A light grey
    (0xFF, 0x8A, 0xD8),  # B pink
    (0x2D, 0xD5, 0x24),  # C green
    (0xFF, 0xF2, 0x2B),  # D yellow
    (0x67, 0xF7, 0xB6),  # E aqua
    (0xFF, 0xFF, 0xFF),  # F white
)

# Source-art matching swatches are intentionally less saturated than the
# nominal display palette. They keep muted authored colors chromatic instead
# of incorrectly mapping them to one of the greys.
DHGR_MATCH_PALETTE = (
    (0x00, 0x00, 0x00),
    (0xBE, 0x19, 0x7D),
    (0x28, 0x28, 0xB4),
    (0x82, 0x37, 0xA0),
    (0x00, 0x64, 0x23),
    (0x64, 0x64, 0x64),
    (0x23, 0x8C, 0xDC),
    (0x8C, 0xBE, 0xE6),
    (0x87, 0x4B, 0x19),
    (0xEB, 0x78, 0x0A),
    (0xA0, 0xA0, 0xA0),
    (0xD7, 0x50, 0x6E),
    (0x46, 0xC8, 0x32),
    (0xEB, 0xDC, 0x3C),
    (0x5A, 0xDC, 0xB4),
    (0xFF, 0xFF, 0xFF),
)

# The lo-res color number is phase-remapped before it becomes the repeating
# four-bit DHGR signal. This swaps color-number bits 1 and 3.
DHGR_WIRE_PATTERNS = (
    0x0, 0x1, 0x8, 0x9, 0x4, 0x5, 0xC, 0xD,
    0x2, 0x3, 0xA, 0xB, 0x6, 0x7, 0xE, 0xF,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--main", required=True)
    parser.add_argument("--aux", required=True)
    parser.add_argument("--preview", required=True)
    parser.add_argument("--height", type=int, default=VISIBLE_HEIGHT)
    parser.add_argument(
        "--dither",
        choices=("none", "floyd-steinberg"),
        default="none",
        help="Palette dithering; flat game art normally looks best with none.",
    )
    return parser.parse_args()


def hgr_offset(y: int) -> int:
    return ((y & 0x07) << 10) + ((y >> 3) & 0x07) * 0x80 + (y >> 6) * 0x28


def make_pillow_palette() -> Image.Image:
    palette = Image.new("P", (1, 1))
    entries = [channel for color in DHGR_PALETTE for channel in color]
    entries.extend([0] * (768 - len(entries)))
    palette.putpalette(entries)
    return palette


def nearest_palette_color(rgb: tuple[int, int, int]) -> int:
    red, green, blue = (channel / 255.0 for channel in rgb)
    hue, saturation, value = colorsys.rgb_to_hsv(red, green, blue)

    if value < 0.06:
        return 0

    neutral_colors = (0, 5, 10, 15)
    candidates = range(16) if saturation >= 0.12 else neutral_colors
    best_color = 0
    best_distance = float("inf")

    for color in candidates:
        pr, pg, pb = (channel / 255.0 for channel in DHGR_MATCH_PALETTE[color])
        ph, ps, pv = colorsys.rgb_to_hsv(pr, pg, pb)
        if saturation < 0.12:
            distance = (value - pv) ** 2
        else:
            hue_distance = abs(hue - ph)
            hue_distance = min(hue_distance, 1.0 - hue_distance)
            distance = (
                4.0 * hue_distance * hue_distance
                + 0.5 * (saturation - ps) ** 2
                + 0.5 * (value - pv) ** 2
            )
        if distance < best_distance:
            best_color = color
            best_distance = distance

    return best_color


def quantize_source(image: Image.Image, dither: str) -> Image.Image:
    if dither == "floyd-steinberg":
        return image.quantize(
            palette=make_pillow_palette(),
            dither=Image.Dither.FLOYDSTEINBERG,
        )

    indexed = Image.new("P", image.size)
    indexed.putpalette(make_pillow_palette().getpalette())
    cache: dict[tuple[int, int, int], int] = {}
    source_pixels = image.load()
    output_pixels = indexed.load()
    for y in range(image.height):
        for x in range(image.width):
            rgb = source_pixels[x, y]
            color = cache.get(rgb)
            if color is None:
                color = nearest_palette_color(rgb)
                cache[rgb] = color
            output_pixels[x, y] = color
    return indexed


def render_source(image_path: Path, height: int, dither: str) -> Image.Image:
    if not 1 <= height <= PAGE_HEIGHT:
        raise ValueError(f"height must be between 1 and {PAGE_HEIGHT}")

    image = Image.open(image_path).convert("RGB")

    # Build at twice the logical width before reducing to 140 colour blocks.
    # This preserves the Apple II screen aspect ratio during source fitting.
    fitted = ImageOps.contain(image, (PAGE_WIDTH * 2, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (PAGE_WIDTH * 2, height), (0, 0, 0))
    canvas.paste(fitted, ((canvas.width - fitted.width) // 2, (height - fitted.height) // 2))
    logical = canvas.resize((PAGE_WIDTH, height), Image.Resampling.LANCZOS)

    return quantize_source(logical, dither)


def to_pages(indexed: Image.Image) -> tuple[bytes, bytes]:
    main = bytearray(PAGE_BYTES)
    aux = bytearray(PAGE_BYTES)
    pixels = indexed.load()

    for y in range(indexed.height):
        signal_bits: list[int] = []
        for x in range(PAGE_WIDTH):
            color = int(pixels[x, y]) & 0x0F
            pattern = DHGR_WIRE_PATTERNS[color]
            signal_bits.extend((pattern >> bit) & 1 for bit in range(3, -1, -1))

        row = hgr_offset(y)
        for byte_index in range(80):
            value = 0
            for bit in range(7):
                value |= signal_bits[byte_index * 7 + bit] << bit
            if byte_index & 1:
                main[row + byte_index // 2] = value
            else:
                aux[row + byte_index // 2] = value

    return bytes(main), bytes(aux)


def decode_pages(main: bytes, aux: bytes, height: int) -> Image.Image:
    preview = Image.new("P", (PAGE_WIDTH, height))
    preview.putpalette(make_pillow_palette().getpalette())
    pixels = preview.load()

    for y in range(height):
        row = hgr_offset(y)
        signal_bits: list[int] = []
        for byte_index in range(80):
            source = main if byte_index & 1 else aux
            value = source[row + byte_index // 2]
            signal_bits.extend((value >> bit) & 1 for bit in range(7))
        for x in range(PAGE_WIDTH):
            color = 0
            for bit in range(4):
                color |= signal_bits[x * 4 + bit] << (3 - bit)
            pixels[x, y] = DHGR_WIRE_PATTERNS[color]

    return preview


def main() -> None:
    args = parse_args()
    indexed = render_source(Path(args.input), args.height, args.dither)
    main_page, aux_page = to_pages(indexed)

    main_path = Path(args.main)
    aux_path = Path(args.aux)
    preview_path = Path(args.preview)
    main_path.parent.mkdir(parents=True, exist_ok=True)
    aux_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    main_path.write_bytes(main_page)
    aux_path.write_bytes(aux_page)

    preview = decode_pages(main_page, aux_page, indexed.height).convert("RGB")
    preview.resize((PAGE_WIDTH * 2, indexed.height), Image.Resampling.NEAREST).save(preview_path)


if __name__ == "__main__":
    main()
