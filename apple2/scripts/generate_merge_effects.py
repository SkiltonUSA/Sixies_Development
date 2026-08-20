#!/usr/bin/env python3
"""Convert merge callouts into compact monochrome DHGR screen fragments."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


EFFECT_NAMES = (
    "awesome",
    "boom",
    "dang",
    "fives",
    "lets_go",
    "sixies",
    "whoa",
    "yeah",
    "wow",
    "yes",
)
EFFECT_FILENAMES = tuple(f"FX{index:02d}" for index in range(len(EFFECT_NAMES)))
SCREEN_WIDTH = 560
SCREEN_HEIGHT = 192
EFFECT_WIDTH = 280
EFFECT_HEIGHT = 48
EFFECT_LEFT = 0
EFFECT_TOP = 56
SEQUENCE_FIRST = EFFECT_LEFT // 7
SEQUENCE_BYTES = EFFECT_WIDTH // 7
BANK_BYTE_OFFSET = SEQUENCE_FIRST // 2
BANK_ROW_BYTES = SEQUENCE_BYTES // 2
BANK_BYTES = BANK_ROW_BYTES * EFFECT_HEIGHT
EFFECT_BYTES = BANK_BYTES * 2
STAR_WIDTH = 24
STAR_HEIGHT = 24
STAR_SIGNAL_WIDTH = STAR_WIDTH * 2
STAR_ACTIVE_TOP = 4
STAR_ACTIVE_HEIGHT = 11
STAR_SEQUENCE_BYTES = 8
STAR_PHASES = 7
STAR_PHASE_BYTES = STAR_SEQUENCE_BYTES * STAR_ACTIVE_HEIGHT
STAR_BYTES = STAR_PHASE_BYTES * STAR_PHASES

# The C64's 24x21 single-color merge-firework sprite, padded to one board tile.
C64_STAR_ROWS = (
    0x000000, 0x000000, 0x000000, 0x000000,
    0x001800, 0x001800, 0x021840, 0x013C80,
    0x00FF00, 0x03FFC0, 0x00FF00, 0x013C80,
    0x021840, 0x001800, 0x001800, 0x000000,
    0x000000, 0x000000, 0x000000, 0x000000,
    0x000000, 0x000000, 0x000000, 0x000000,
)


def hgr_address(y: int) -> int:
    return 0x2000 + ((y & 0x07) << 10) + (((y >> 3) & 0x07) << 7) + (y >> 6) * 0x28


def render_mask(path: Path) -> Image.Image:
    source = Image.open(path).convert("RGB")
    source_pixels = source.load()
    mask = Image.new("L", source.size, 0)
    mask_pixels = mask.load()
    for y in range(source.height):
        for x in range(source.width):
            mask_pixels[x, y] = 255 if max(source_pixels[x, y]) >= 72 else 0

    # DHGR signal pixels are much narrower than scanlines on a 4:3 display.
    aspect_corrected = mask.resize((mask.width * 2, mask.height), Image.Resampling.NEAREST)
    fitted = ImageOps.contain(
        aspect_corrected,
        (EFFECT_WIDTH, EFFECT_HEIGHT),
        Image.Resampling.LANCZOS,
    ).point(lambda value: 255 if value >= 96 else 0)
    canvas = Image.new("L", (EFFECT_WIDTH, EFFECT_HEIGHT), 0)
    canvas.paste(
        fitted,
        ((EFFECT_WIDTH - fitted.width) // 2, (EFFECT_HEIGHT - fitted.height) // 2),
    )
    return canvas


def pack_banks(mask: Image.Image) -> tuple[bytes, bytes]:
    if mask.size != (EFFECT_WIDTH, EFFECT_HEIGHT):
        raise ValueError("merge effect mask has an unexpected size")
    auxiliary = bytearray(BANK_BYTES)
    main = bytearray(BANK_BYTES)
    pixels = mask.load()
    for y in range(EFFECT_HEIGHT):
        for local_x in range(EFFECT_WIDTH):
            if pixels[local_x, y] == 0:
                continue
            signal = EFFECT_LEFT + local_x
            sequence_byte = signal // 7
            bank = auxiliary if sequence_byte & 1 == 0 else main
            bank_byte = sequence_byte // 2 - BANK_BYTE_OFFSET
            bank[y * BANK_ROW_BYTES + bank_byte] |= 1 << (signal % 7)
    return bytes(auxiliary), bytes(main)


def build_star_mask() -> bytearray:
    mask = bytearray(STAR_SIGNAL_WIDTH * STAR_HEIGHT)
    for y, bits in enumerate(C64_STAR_ROWS):
        for x in range(STAR_WIDTH):
            if bits & (1 << (STAR_WIDTH - 1 - x)):
                mask[y * STAR_SIGNAL_WIDTH + x * 2] = 1
                mask[y * STAR_SIGNAL_WIDTH + x * 2 + 1] = 1
    return mask


def render_star_phase(mask: bytearray, phase: int) -> bytes:
    if phase < 0 or phase >= STAR_PHASES:
        raise ValueError("merge star phase must be 0-6")
    blit = bytearray(STAR_PHASE_BYTES)
    for y in range(STAR_ACTIVE_TOP, STAR_ACTIVE_TOP + STAR_ACTIVE_HEIGHT):
        for local_signal in range(STAR_SIGNAL_WIDTH):
            if not mask[y * STAR_SIGNAL_WIDTH + local_signal]:
                continue
            shifted_signal = phase + local_signal
            target = (
                (y - STAR_ACTIVE_TOP) * STAR_SEQUENCE_BYTES
                + shifted_signal // 7
            )
            blit[target] |= 1 << (shifted_signal % 7)
    return bytes(blit)


def build_star_blits() -> bytes:
    mask = build_star_mask()
    blits = bytearray()
    for phase in range(STAR_PHASES):
        blits.extend(render_star_phase(mask, phase))
    if len(blits) != STAR_BYTES:
        raise AssertionError("unexpected merge star size")
    return bytes(blits)


def write_preview(path: Path, mask: Image.Image) -> None:
    preview = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 0)
    preview.paste(mask, (EFFECT_LEFT, EFFECT_TOP))
    path.parent.mkdir(parents=True, exist_ok=True)
    preview.resize((SCREEN_WIDTH, SCREEN_HEIGHT * 2), Image.Resampling.NEAREST).save(path)


def write_star_preview(path: Path) -> None:
    mask = build_star_mask()
    preview = Image.new("L", (SCREEN_WIDTH, SCREEN_HEIGHT), 0)
    pixels = preview.load()
    for y in range(STAR_HEIGHT):
        for x in range(STAR_SIGNAL_WIDTH):
            if mask[y * STAR_SIGNAL_WIDTH + x]:
                pixels[128 * 2 + x, 68 + y] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    preview.resize((SCREEN_WIDTH, SCREEN_HEIGHT * 2), Image.Resampling.NEAREST).save(path)


def format_array(name: str, values: list[int]) -> str:
    lines = [f"const unsigned char {name}[{len(values)}] = {{"]
    for offset in range(0, len(values), 12):
        row = ", ".join(f"0x{value:02X}" for value in values[offset : offset + 12])
        lines.append(f"    {row},")
    lines.append("};")
    return "\n".join(lines)


def write_header(path: Path) -> None:
    sections = [
        "#ifndef SIXIES_MERGE_EFFECTS_H",
        "#define SIXIES_MERGE_EFFECTS_H",
        "",
        f"#define MERGE_EFFECT_COUNT {len(EFFECT_NAMES)}",
        f"#define MERGE_EFFECT_WIDTH {EFFECT_WIDTH}",
        f"#define MERGE_EFFECT_HEIGHT {EFFECT_HEIGHT}",
        f"#define MERGE_EFFECT_BANK_ROW_BYTES {BANK_ROW_BYTES}",
        f"#define MERGE_EFFECT_BANK_BYTES {BANK_BYTES}",
        f"#define MERGE_EFFECT_BYTES {EFFECT_BYTES}",
        f"#define MERGE_EFFECT_BYTE_OFFSET {BANK_BYTE_OFFSET}",
        f"#define MERGE_STAR_ACTIVE_TOP {STAR_ACTIVE_TOP}",
        f"#define MERGE_STAR_ACTIVE_HEIGHT {STAR_ACTIVE_HEIGHT}",
        f"#define MERGE_STAR_SEQUENCE_BYTES {STAR_SEQUENCE_BYTES}",
        f"#define MERGE_STAR_PHASES {STAR_PHASES}",
        f"#define MERGE_STAR_PHASE_BYTES {STAR_PHASE_BYTES}",
        f"#define MERGE_STAR_BYTES {STAR_BYTES}",
        "",
        "#endif",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sections), encoding="ascii")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in EFFECT_NAMES:
        parser.add_argument(f"--{name.replace('_', '-')}", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--preview-dir", required=True, type=Path)
    parser.add_argument("--header", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.preview_dir.mkdir(parents=True, exist_ok=True)
    star_blits = build_star_blits()
    (args.output_dir / "MERGESTAR").write_bytes(star_blits)
    for name, filename in zip(EFFECT_NAMES, EFFECT_FILENAMES):
        source = getattr(args, name)
        mask = render_mask(source)
        auxiliary, main = pack_banks(mask)
        data = auxiliary + main
        if len(data) != EFFECT_BYTES:
            raise AssertionError("unexpected merge effect size")
        (args.output_dir / filename).write_bytes(data)
        write_preview(args.preview_dir / f"merge_{name}.png", mask)
    write_star_preview(args.preview_dir / "merge_star.png")
    write_header(args.header)


if __name__ == "__main__":
    main()
