#!/usr/bin/env python3
"""Convert and RLE-pack the Studio313 monochrome DHGR presentation screen."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from PIL import Image, ImageOps


SCRIPT_DIR = Path(__file__).parent
IMPORTER_SPEC = importlib.util.spec_from_file_location(
    "import_a2fm_asset", SCRIPT_DIR / "import_a2fm_asset.py"
)
assert IMPORTER_SPEC is not None and IMPORTER_SPEC.loader is not None
A2FM = importlib.util.module_from_spec(IMPORTER_SPEC)
IMPORTER_SPEC.loader.exec_module(A2FM)

MAX_PACKED_BYTES = 8400


def render_mono_source(image_path: Path) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    fitted = ImageOps.contain(
        image,
        (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT * 2),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new(
        "RGB",
        (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT * 2),
        (0, 0, 0),
    )
    canvas.paste(
        fitted,
        ((canvas.width - fitted.width) // 2, (canvas.height - fitted.height) // 2),
    )
    logical = canvas.resize(
        (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT),
        Image.Resampling.LANCZOS,
    )
    return ImageOps.grayscale(logical).convert(
        "1",
        dither=Image.Dither.FLOYDSTEINBERG,
    ).convert("L")


def to_mono_pages(image: Image.Image) -> tuple[bytes, bytes]:
    if image.size != (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT):
        raise ValueError("presentation must be 560x192")

    main = bytearray(A2FM.PAGE_BYTES)
    auxiliary = bytearray(A2FM.PAGE_BYTES)
    pixels = image.load()
    for y in range(A2FM.SCREEN_HEIGHT):
        row = A2FM.hgr_offset(y)
        for group in range(80):
            value = 0
            for bit in range(7):
                if pixels[group * 7 + bit, y] >= 128:
                    value |= 1 << bit
            destination = main if group & 1 else auxiliary
            destination[row + group // 2] = value
    return bytes(main), bytes(auxiliary)


def pack_rle(data: bytes) -> bytes:
    output = bytearray()
    position = 0
    while position < len(data):
        run = 1
        while (
            position + run < len(data)
            and run < 128
            and data[position + run] == data[position]
        ):
            run += 1
        if run >= 3:
            output.extend((0x80 | (run - 1), data[position]))
            position += run
            continue

        start = position
        position += run
        while position < len(data) and position - start < 128:
            run = 1
            while (
                position + run < len(data)
                and run < 128
                and data[position + run] == data[position]
            ):
                run += 1
            if run >= 3:
                break
            position += run
        literal = data[start:position]
        output.append(len(literal) - 1)
        output.extend(literal)
    return bytes(output)


def unpack_rle(data: bytes, expected_size: int) -> bytes:
    output = bytearray()
    position = 0
    while position < len(data):
        token = data[position]
        position += 1
        count = (token & 0x7F) + 1
        if token & 0x80:
            if position >= len(data):
                raise ValueError("RLE repeat token has no value")
            output.extend((data[position],) * count)
            position += 1
        else:
            end = position + count
            if end > len(data):
                raise ValueError("RLE literal exceeds input")
            output.extend(data[position:end])
            position = end
    if len(output) != expected_size:
        raise ValueError(f"RLE output is {len(output)} bytes, expected {expected_size}")
    return bytes(output)


def format_header(auxiliary_size: int, main_size: int, checksum: int) -> str:
    total = auxiliary_size + main_size
    return "\n".join(
        (
            "#ifndef SIXIES_PRESENTS_ASSETS_H",
            "#define SIXIES_PRESENTS_ASSETS_H",
            "",
            f"#define PRESENTS_AUX_PACKED_BYTES {auxiliary_size}u",
            f"#define PRESENTS_MAIN_PACKED_BYTES {main_size}u",
            f"#define PRESENTS_PACKED_BYTES {total}u",
            f"#define PRESENTS_PACKED_CHECKSUM {checksum}u",
            "",
            "#endif",
            "",
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--header", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    monochrome = render_mono_source(args.input)
    main_page, auxiliary_page = to_mono_pages(monochrome)
    packed_auxiliary = pack_rle(auxiliary_page)
    packed_main = pack_rle(main_page)
    packed = packed_auxiliary + packed_main
    if len(packed) > MAX_PACKED_BYTES:
        raise ValueError(
            f"packed presentation is {len(packed)} bytes; limit is {MAX_PACKED_BYTES}"
        )
    if unpack_rle(packed_auxiliary, A2FM.PAGE_BYTES) != auxiliary_page:
        raise AssertionError("auxiliary presentation RLE did not round trip")
    if unpack_rle(packed_main, A2FM.PAGE_BYTES) != main_page:
        raise AssertionError("main presentation RLE did not round trip")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.header.parent.mkdir(parents=True, exist_ok=True)
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(packed)
    args.header.write_text(
        format_header(len(packed_auxiliary), len(packed_main), sum(packed) & 0xFFFF),
        encoding="ascii",
    )
    A2FM.decode_mono(main_page, auxiliary_page).resize(
        (A2FM.SCREEN_WIDTH, A2FM.SCREEN_HEIGHT * 2),
        Image.Resampling.NEAREST,
    ).save(args.preview)


if __name__ == "__main__":
    main()
