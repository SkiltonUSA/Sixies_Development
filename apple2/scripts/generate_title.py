#!/usr/bin/env python3
"""Add the start prompt to the supplied monochrome DHGR title screen."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A2FM = load_module("import_a2fm_asset", SCRIPT_DIR / "import_a2fm_asset.py")
INSTRUCTIONS = load_module(
    "generate_instructions", SCRIPT_DIR / "generate_instructions.py"
)

PROMPT = "PRESS SPACE"
PROMPT_Y = 168
PROMPT_CELL_WIDTH = 7


def draw_prompt(image: Image.Image) -> None:
    width = len(PROMPT) * PROMPT_CELL_WIDTH - 2
    x = (A2FM.SCREEN_WIDTH - width) // 2
    pixels = image.load()
    for character in PROMPT:
        rows = INSTRUCTIONS.FONT[character]
        for row, bits in enumerate(rows):
            for column in range(5):
                if bits & (1 << (4 - column)):
                    pixels[x + column, PROMPT_Y + row] = 255
        x += PROMPT_CELL_WIDTH


def render_title(source: bytes) -> tuple[bytes, bytes, Image.Image]:
    main_page, auxiliary_page = A2FM.split_a2fm(source)
    image = A2FM.decode_mono(main_page, auxiliary_page)
    draw_prompt(image)
    main_page, auxiliary_page = INSTRUCTIONS.GENERATOR.to_mono_pages(image)
    return main_page, auxiliary_page, image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    main_page, auxiliary_page, image = render_title(args.input.read_bytes())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    # b2d A2FM stores the auxiliary bank before the main bank.
    args.output.write_bytes(auxiliary_page + main_page)
    image.resize(
        (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT * 2),
        Image.Resampling.NEAREST,
    ).save(args.preview)


if __name__ == "__main__":
    main()
