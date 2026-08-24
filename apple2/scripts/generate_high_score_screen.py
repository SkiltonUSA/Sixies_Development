#!/usr/bin/env python3
"""Generate the DHGR high-score background and disk-backed live font."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps


SCRIPT_DIR = Path(__file__).parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INSTRUCTIONS = load_module(
    "generate_instructions", SCRIPT_DIR / "generate_instructions.py"
)
GENERATOR = INSTRUCTIONS.GENERATOR

SCREEN_WIDTH = GENERATOR.A2FM.SCREEN_WIDTH
SCREEN_HEIGHT = GENERATOR.A2FM.SCREEN_HEIGHT
FONT_ROWS = 7
FONT_CELL_SIGNALS = 14
FONT_GLYPH_BYTES = FONT_ROWS * 2
TABLE_COLUMN = 11
NAME_COLUMN = TABLE_COLUMN + 5
SCORE_COLUMN = TABLE_COLUMN + 10
TABLE_TOP = 51
TABLE_ROW_PITCH = 10
GLYPHS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ .>-"
SEEDED_ROWS = (
    ("DOM", 1349),
    ("PRI", 1020),
    ("TWD", 893),
    ("TAN", 802),
    ("TB ", 755),
    ("ACE", 650),
    ("MAX", 540),
    ("ZED", 430),
    ("BOT", 320),
    ("CPU", 210),
)
GREATER_ROWS = (0x10, 0x08, 0x04, 0x02, 0x04, 0x08, 0x10)
ART_MONO_THRESHOLD = 100
MASCOT_CONTENT_THRESHOLD = 24
MASCOT_SIZE = (148, 90)
MASCOT_POSITION = (2, 55)


def glyph_rows(character: str) -> tuple[int, ...]:
    if character == ">":
        return GREATER_ROWS
    return INSTRUCTIONS.FONT[character]


def draw_text_at(image: Image.Image, text: str, x: int, y: int) -> None:
    pixels = image.load()
    for character in text:
        for row, bits in enumerate(glyph_rows(character)):
            for column in range(5):
                if bits & (1 << (4 - column)):
                    signal = x + column * 2
                    pixels[signal, y + row] = 255
                    pixels[signal + 1, y + row] = 255
        x += INSTRUCTIONS.CELL_WIDTH


def draw_runtime_text(image: Image.Image, text: str, column: int, y: int) -> None:
    pixels = image.load()
    for character_index, character in enumerate(text):
        left = (column + character_index) * FONT_CELL_SIGNALS + 2
        for row, bits in enumerate(glyph_rows(character)):
            for glyph_column in range(5):
                if bits & (1 << (4 - glyph_column)):
                    signal = left + glyph_column * 2
                    pixels[signal, y + row] = 255
                    pixels[signal + 1, y + row] = 255


def monochrome_art(
    path: Path,
    source_size: tuple[int, int],
    output_size: tuple[int, int],
) -> Image.Image:
    source = Image.open(path).convert("RGB")
    if source.size != source_size:
        raise ValueError(f"high-score art must be {source_size}, got {source.size}")
    mono = Image.new("L", source.size, 0)
    source_pixels = source.load()
    mono_pixels = mono.load()
    for y in range(source.height):
        for x in range(source.width):
            mono_pixels[x, y] = (
                255 if max(source_pixels[x, y]) >= ART_MONO_THRESHOLD else 0
            )
    return mono.resize(output_size, Image.Resampling.NEAREST)


def monochrome_dice(path: Path) -> Image.Image:
    return monochrome_art(path, (64, 56), (128, 56))


def monochrome_mascot(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGB")
    if source.size != (1414, 1113):
        raise ValueError(f"high-score mascot must be 1414x1113, got {source.size}")

    intensity = ImageChops.lighter(
        ImageChops.lighter(source.getchannel("R"), source.getchannel("G")),
        source.getchannel("B"),
    )
    content_bounds = intensity.point(
        lambda value: 255 if value >= MASCOT_CONTENT_THRESHOLD else 0
    ).getbbox()
    if content_bounds is None:
        raise ValueError("high-score mascot has no visible pixels")

    physical_size = (MASCOT_SIZE[0], MASCOT_SIZE[1] * 2)
    fitted = ImageOps.contain(
        intensity.crop(content_bounds),
        physical_size,
        Image.Resampling.LANCZOS,
    )
    physical_canvas = Image.new("L", physical_size, 0)
    physical_canvas.paste(
        fitted,
        (
            (physical_canvas.width - fitted.width) // 2,
            (physical_canvas.height - fitted.height) // 2,
        ),
    )
    return physical_canvas.resize(
        MASCOT_SIZE,
        Image.Resampling.LANCZOS,
    ).convert(
        "1",
        dither=Image.Dither.FLOYDSTEINBERG,
    ).convert(
        "L"
    )


def render_background(dice_path: Path, mascot_path: Path) -> Image.Image:
    image = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 0)
    draw = ImageDraw.Draw(image)

    INSTRUCTIONS.draw_text(image, "SIXIES HIGH SCORES", 12)
    draw.line((24, 29, 535, 29), fill=255)

    draw_text_at(image, "RANK  NAME  SCORE", 171, 39)
    for index in range(10):
        draw_runtime_text(
            image,
            f" {index + 1:2d}. ",
            TABLE_COLUMN,
            TABLE_TOP + index * TABLE_ROW_PITCH,
        )

    image.paste(monochrome_mascot(mascot_path), MASCOT_POSITION)
    image.paste(monochrome_dice(dice_path), (403, 60))

    INSTRUCTIONS.draw_text(image, "SPACE RETURN OR N STARTS A NEW GAME", 173)
    return image


def build_font() -> bytes:
    output = bytearray()
    for character in GLYPHS:
        auxiliary = bytearray(FONT_ROWS)
        main = bytearray(FONT_ROWS)
        for row, bits in enumerate(glyph_rows(character)):
            for column in range(5):
                if not bits & (1 << (4 - column)):
                    continue
                for repeat in range(2):
                    signal = 2 + column * 2 + repeat
                    if signal < 7:
                        auxiliary[row] |= 1 << signal
                    else:
                        main[row] |= 1 << (signal - 7)
        output.extend(auxiliary)
        output.extend(main)
    return bytes(output)


def format_header(background_header: str, font: bytes) -> str:
    lines = background_header.rstrip().splitlines()
    lines.pop(-1)
    lines.extend(
        (
            f"#define HIGH_SCORE_FONT_BYTES {len(font)}u",
            f"#define HIGH_SCORE_FONT_CHECKSUM {sum(font) & 0xFFFF}u",
            f"#define HIGH_SCORE_FONT_GLYPH_BYTES {FONT_GLYPH_BYTES}u",
            f"#define HIGH_SCORE_FONT_ROWS {FONT_ROWS}u",
            f"#define HIGH_SCORE_FONT_GLYPH_COUNT {len(GLYPHS)}u",
            f"#define HIGH_SCORE_TABLE_COLUMN {TABLE_COLUMN}u",
            f"#define HIGH_SCORE_NAME_COLUMN {NAME_COLUMN}u",
            f"#define HIGH_SCORE_SCORE_COLUMN {SCORE_COLUMN}u",
            f"#define HIGH_SCORE_TABLE_TOP {TABLE_TOP}u",
            f"#define HIGH_SCORE_TABLE_ROW_PITCH {TABLE_ROW_PITCH}u",
            "",
            "#endif",
            "",
        )
    )
    return "\n".join(lines)


def sample_line(index: int, name: str, score: int) -> str:
    return f" {index + 1:2d}. {name}  {score:5d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dice", required=True, type=Path)
    parser.add_argument("--mascot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--font", required=True, type=Path)
    parser.add_argument("--header", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    background = render_background(args.dice, args.mascot)
    main_page, auxiliary_page = GENERATOR.to_mono_pages(background)
    GENERATOR.write_packed_screen(
        main_page,
        auxiliary_page,
        args.output,
        args.header,
        None,
        "HIGH_SCORE",
    )

    font = build_font()
    args.font.parent.mkdir(parents=True, exist_ok=True)
    args.font.write_bytes(font)
    args.header.write_text(
        format_header(args.header.read_text(encoding="ascii"), font),
        encoding="ascii",
    )

    preview = background.copy()
    for index, (name, score) in enumerate(SEEDED_ROWS):
        y = TABLE_TOP + index * TABLE_ROW_PITCH
        draw_runtime_text(preview, name, NAME_COLUMN, y)
        draw_runtime_text(preview, f"{score:5d}", SCORE_COLUMN, y)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    preview.resize(
        (SCREEN_WIDTH, SCREEN_HEIGHT * 2),
        Image.Resampling.NEAREST,
    ).save(args.preview)


if __name__ == "__main__":
    main()
