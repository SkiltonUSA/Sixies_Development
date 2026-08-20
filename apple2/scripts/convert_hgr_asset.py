#!/usr/bin/env python3
"""Convert source art into Apple II hi-res page data and a preview image."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


PAGE_WIDTH = 280
PAGE_HEIGHT = 192
PAGE_BYTES = 8192


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--header", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--preview", required=True)
    parser.add_argument("--width", type=int, default=280)
    parser.add_argument("--height", type=int, default=160)
    return parser.parse_args()


def hgr_offset(y: int) -> int:
    return ((y & 0x07) << 10) + ((y >> 3) & 0x07) * 0x80 + (y >> 6) * 0x28


def estimate_background(image: Image.Image) -> tuple[int, int, int]:
    width, height = image.size
    samples = [
        image.getpixel((0, 0)),
        image.getpixel((width - 1, 0)),
        image.getpixel((0, height - 1)),
        image.getpixel((width - 1, height - 1)),
        image.getpixel((width // 2, 0)),
        image.getpixel((width // 2, height - 1)),
    ]
    r = sum(pixel[0] for pixel in samples) // len(samples)
    g = sum(pixel[1] for pixel in samples) // len(samples)
    b = sum(pixel[2] for pixel in samples) // len(samples)
    return (r, g, b)


def build_mask(image: Image.Image) -> Image.Image:
    bg = estimate_background(image)
    bg_image = Image.new("RGB", image.size, bg)
    diff = ImageChops.difference(image, bg_image).convert("L")
    diff = ImageOps.autocontrast(diff, cutoff=1)
    return diff.point(lambda value: 255 if value >= 26 else 0, mode="1")


def render_source(image_path: Path, width: int, height: int) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    fitted = ImageOps.contain(image, (width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), estimate_background(image))
    x = (width - fitted.width) // 2
    y = (height - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    mask = build_mask(canvas)
    mono = Image.new("1", (width, height), 0)
    mono.paste(1, mask=mask)
    return mono


def to_page(mono: Image.Image) -> bytes:
    page = bytearray(PAGE_BYTES)
    x_offset = (PAGE_WIDTH - mono.width) // 2
    y_offset = 0
    pixels = mono.load()
    for y in range(mono.height):
        row = hgr_offset(y + y_offset)
        for x in range(mono.width):
            if pixels[x, y]:
                page[row + ((x + x_offset) // 7)] |= 1 << ((x + x_offset) % 7)
    return bytes(page)


def write_header(symbol: str, page: bytes, output: Path) -> None:
    guard = f"GENERATED_{symbol.upper()}_H"
    lines = [
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
        "static const unsigned char " + symbol + f"[{len(page)}] = {{",
    ]
    for start in range(0, len(page), 12):
        chunk = ", ".join(f"0x{value:02x}" for value in page[start:start + 12])
        lines.append("    " + chunk + ",")
    lines.extend(
        [
            "};",
            "",
            f"#define {symbol.upper()}_SIZE {len(page)}",
            "",
            f"#endif /* {guard} */",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="ascii")


def write_preview(mono: Image.Image, output: Path) -> None:
    preview = Image.new("RGB", mono.size, (0, 0, 0))
    preview.paste((255, 255, 255), mask=mono.convert("L"))
    output.parent.mkdir(parents=True, exist_ok=True)
    preview.save(output)


def main() -> None:
    args = parse_args()
    mono = render_source(Path(args.input), args.width, args.height)
    page = to_page(mono)
    header_path = Path(args.header)
    header_path.parent.mkdir(parents=True, exist_ok=True)
    write_header(args.symbol, page, header_path)
    write_preview(mono, Path(args.preview))


if __name__ == "__main__":
    main()
