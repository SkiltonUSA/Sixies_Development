#!/usr/bin/env python3
"""Generate the title-compatible monochrome DHGR game-over screen."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


SCRIPT_DIR = Path(__file__).parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR = load_module("generate_presents", SCRIPT_DIR / "generate_presents.py")
A2FM = GENERATOR.A2FM
ART_HEIGHT = 160
CONTENT_THRESHOLD = 24


def render_game_over(image_path: Path) -> Image.Image:
    source = Image.open(image_path).convert("RGB")
    intensity = ImageChops.lighter(
        ImageChops.lighter(source.getchannel("R"), source.getchannel("G")),
        source.getchannel("B"),
    )
    content_bounds = intensity.point(
        lambda value: 255 if value >= CONTENT_THRESHOLD else 0
    ).getbbox()
    if content_bounds is None:
        raise ValueError("game-over artwork has no visible pixels")

    fitted = ImageOps.contain(
        intensity.crop(content_bounds),
        (A2FM.SCREEN_WIDTH, ART_HEIGHT * 2),
        Image.Resampling.LANCZOS,
    )
    physical_canvas = Image.new("L", (A2FM.SCREEN_WIDTH, ART_HEIGHT * 2), 0)
    physical_canvas.paste(
        fitted,
        (
            (physical_canvas.width - fitted.width) // 2,
            (physical_canvas.height - fitted.height) // 2,
        ),
    )
    logical = physical_canvas.resize(
        (A2FM.SCREEN_WIDTH, ART_HEIGHT),
        Image.Resampling.LANCZOS,
    )
    monochrome = logical.convert(
        "1",
        dither=Image.Dither.FLOYDSTEINBERG,
    ).convert("L")

    screen = Image.new("L", (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT), 0)
    screen.paste(monochrome, (0, 0))
    return screen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--header", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image = render_game_over(args.input)
    main_page, auxiliary_page = GENERATOR.to_mono_pages(image)
    GENERATOR.write_packed_screen(
        main_page,
        auxiliary_page,
        args.output,
        args.header,
        args.preview,
        "GAME_OVER",
    )


if __name__ == "__main__":
    main()
