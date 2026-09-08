#!/usr/bin/env python3
"""Turn a RastaConverter preview into Sixies' compact ANTIC-E title assets.

RastaConverter's full per-scanline kernel overlaps the 64K game's program RAM.
This post-process retains its converted image, then selects three hardware
colors for the complete frame. The game supplies black as the fourth color,
so the title needs no raster interrupts and remains stable beside POKEY music.
"""

from __future__ import annotations

import argparse
import importlib.util
from itertools import combinations
from pathlib import Path

from PIL import Image


WIDTH = 320
HEIGHT = 192
BAND_HEIGHT = HEIGHT
ART_SIZE = (264, 124)
ART_TOP = 4


def load_instruction_font(root: Path):
    path = root / "apple2" / "scripts" / "generate_instructions.py"
    spec = importlib.util.spec_from_file_location("sixies_title_font", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load title font from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FONT


def draw_native_text(
    mic: bytearray,
    preview: Image.Image,
    text: str,
    y: int,
    color_index: int,
    color,
    font,
) -> None:
    """Overlay 5x7 text in logical ANTIC-E pixels after image conversion.

    A mode-E pixel is two television pixels wide. Drawing the glyphs directly
    into the packed bitmap avoids the destructive horizontal color-pairing
    that made the earlier source-image text thin and difficult to read.
    """
    logical_width = WIDTH // 2
    advance = 6
    x = (logical_width - (len(text) * advance - 1)) // 2
    preview_pixels = preview.load()
    for character in text:
        glyph = font[character]
        for row, bits in enumerate(glyph):
            for vertical_scale in range(2):
                pixel_y = y + row * 2 + vertical_scale
                for column in range(5):
                    if not bits & (1 << (4 - column)):
                        continue
                    pixel_x = x + column
                    offset = pixel_y * 40 + pixel_x // 4
                    shift = 6 - 2 * (pixel_x % 4)
                    mic[offset] = (mic[offset] & ~(3 << shift)) | (color_index << shift)
                    preview_pixels[pixel_x * 2, pixel_y] = color
                    preview_pixels[pixel_x * 2 + 1, pixel_y] = color
        x += advance


def color_distance(left, right) -> int:
    """Small integer metric suited to the converter's already-quantized RGB."""
    return (
        2 * (left[0] - right[0]) ** 2
        + 3 * (left[1] - right[1]) ** 2
        + (left[2] - right[2]) ** 2
    )


def nearest_code(pixel, palette, codes, cache) -> int:
    if pixel not in cache:
        cache[pixel] = min(codes, key=lambda code: color_distance(pixel, palette[code]))
    return cache[pixel]


def prepare(input_path: Path, palette_path: Path, output_dir: Path) -> None:
    with Image.open(input_path) as source:
        if source.size != (WIDTH, HEIGHT):
            raise ValueError(f"Rasta preview must be 320x192, got {source.size}")
        source = source.convert("RGB")

    # Remove Rasta's unused black margin and refit the complete composition,
    # preserving its proportions while reserving two unobstructed text rows.
    visible = source.convert("L").point(lambda value: 255 if value > 6 else 0)
    bounds = visible.getbbox()
    if bounds is None:
        raise ValueError("Rasta preview contains no visible artwork")
    art = source.crop(bounds).resize(ART_SIZE, Image.Resampling.LANCZOS)
    fitted = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    fitted.paste(art, ((WIDTH - ART_SIZE[0]) // 2, ART_TOP))
    font = load_instruction_font(Path(__file__).resolve().parents[2])

    palette_data = palette_path.read_bytes()
    if len(palette_data) < 768:
        raise ValueError("RastaConverter ACT palette must contain 256 RGB entries")
    palette = [tuple(palette_data[index:index + 3]) for index in range(0, 768, 3)]
    hardware_codes = tuple(range(0, 256, 2))
    nearest_cache = {}

    preview = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    preview_pixels = preview.load()
    source_pixels = fitted.load()
    mic = bytearray()
    band_palette = bytearray()

    for band_top in range(0, HEIGHT, BAND_HEIGHT):
        pairs = [
            (source_pixels[x, y], source_pixels[x + 1, y])
            for y in range(band_top, band_top + BAND_HEIGHT)
            for x in range(0, WIDTH, 2)
        ]
        counts: dict[int, int] = {}
        for pair in pairs:
            for pixel in pair:
                code = nearest_code(pixel, palette, hardware_codes, nearest_cache)
                if code:
                    counts[code] = counts.get(code, 0) + 1
        pool = [
            code
            for code, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]
        ]
        if not pool:
            selected = (0, 0, 0)
        else:
            while len(pool) < 3:
                pool.append(pool[-1])
            selected = min(
                combinations(pool, 3),
                key=lambda choice: sum(
                    min(
                        color_distance(left, palette[code])
                        + color_distance(right, palette[code])
                        for code in (0,) + choice
                    )
                    for left, right in pairs
                ),
            )
        band_palette.extend(selected)
        colors = (0,) + selected

        for y in range(band_top, band_top + BAND_HEIGHT):
            row = bytearray()
            for x in range(0, WIDTH, 2):
                left = source_pixels[x, y]
                right = source_pixels[x + 1, y]
                value = min(
                    range(4),
                    key=lambda index: (
                        color_distance(left, palette[colors[index]])
                        + color_distance(right, palette[colors[index]])
                    ),
                )
                preview_pixels[x, y] = palette[colors[value]]
                preview_pixels[x + 1, y] = palette[colors[value]]
                logical_x = x // 2
                if logical_x % 4 == 0:
                    row.append(0)
                row[-1] |= value << (6 - 2 * (logical_x % 4))
            mic.extend(row)

    if len(mic) != 7680 or len(band_palette) != (HEIGHT // BAND_HEIGHT) * 3:
        raise AssertionError("unexpected ANTIC-E output geometry")

    # These labels are UI, not artwork. Add them after quantization so every
    # glyph pixel maps to one complete ANTIC-E color pair and remains crisp.
    gold_index = min(
        range(1, 4),
        key=lambda index: color_distance(palette[colors[index]], (255, 204, 68)),
    )
    light_index = min(
        range(1, 4),
        key=lambda index: color_distance(palette[colors[index]], (190, 190, 190)),
    )
    draw_native_text(
        mic, preview, "PRESS FIRE TO START", 151,
        gold_index, palette[colors[gold_index]], font,
    )
    draw_native_text(
        mic, preview, "ATARI 800XL 64K", 174,
        light_index, palette[colors[light_index]], font,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "title_rasta.mic").write_bytes(mic)
    (output_dir / "title_rasta.pal").write_bytes(band_palette)
    preview.save(output_dir / "title_rasta_native.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="320x192 RastaConverter output PNG")
    parser.add_argument("palette", type=Path, help="ACT palette used by RastaConverter")
    parser.add_argument("output", type=Path, help="directory for .mic/.pal/preview")
    args = parser.parse_args()
    prepare(args.input, args.palette, args.output)


if __name__ == "__main__":
    main()
