#!/usr/bin/env python3

"""Convert the supplied side-control pictograms into C64 hi-res sprites."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import subprocess
import sys


SPRITE_WIDTH = 24
SPRITE_HEIGHT = 21
ART_WIDTH = 20
ART_HEIGHT = 20
MIN_COMPONENT_SIZE = 100
MAX_ICON_ASPECT = 1.5
FOREGROUND_COVERAGE = 0.25
PREVIEW_SCALE = 12
PREVIEW_COLOR = (0xA9, 0xFF, 0x9F)


def dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x",
            str(path),
        ]
    ).decode("ascii").strip()
    return tuple(int(value) for value in result.split("x"))


def raw_rgb(path: Path) -> bytes:
    return subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-",
        ]
    )


def light_green_mask(rgb: bytes, width: int, height: int) -> bytearray:
    expected = width * height * 3
    if len(rgb) != expected:
        raise ValueError(f"expected {expected} RGB bytes, found {len(rgb)}")
    mask = bytearray(width * height)
    for index, offset in enumerate(range(0, len(rgb), 3)):
        red, green, blue = rgb[offset : offset + 3]
        mask[index] = (
            green >= red + 8
            and green >= blue + 8
            and red + green + blue >= 300
        )
    return mask


def connected_components(mask: bytearray, width: int, height: int):
    seen = bytearray(len(mask))
    components = []
    for start, enabled in enumerate(mask):
        if not enabled or seen[start]:
            continue
        seen[start] = 1
        pending = deque([start])
        members = []
        while pending:
            index = pending.pop()
            members.append(index)
            x = index % width
            y = index // width
            neighbors = (
                index - 1 if x else -1,
                index + 1 if x + 1 < width else -1,
                index - width if y else -1,
                index + width if y + 1 < height else -1,
            )
            for neighbor in neighbors:
                if neighbor >= 0 and mask[neighbor] and not seen[neighbor]:
                    seen[neighbor] = 1
                    pending.append(neighbor)
        if len(members) >= MIN_COMPONENT_SIZE:
            components.append(members)
    return components


def component_bounds(component: list[int], width: int):
    xs = [index % width for index in component]
    ys = [index // width for index in component]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def select_pictogram(mask: bytearray, width: int, height: int, count: int):
    candidates = []
    for component in connected_components(mask, width, height):
        left, top, right, bottom = component_bounds(component, width)
        component_width = right - left
        component_height = bottom - top
        if left >= width * 0.45:
            continue
        if component_width / component_height > MAX_ICON_ASPECT:
            continue
        candidates.append(component)
    candidates.sort(key=len, reverse=True)
    if len(candidates) < count:
        raise ValueError(f"found {len(candidates)} icon components, need {count}")
    selected = bytearray(width * height)
    for component in candidates[:count]:
        for index in component:
            selected[index] = 1
    return selected


def content_bounds(mask: bytearray, width: int):
    points = [index for index, value in enumerate(mask) if value]
    if not points:
        raise ValueError("icon contains no foreground artwork")
    xs = [index % width for index in points]
    ys = [index // width for index in points]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def resize_to_sprite(mask: bytearray, width: int) -> list[list[int]]:
    left, top, right, bottom = content_bounds(mask, width)
    crop_width = right - left
    crop_height = bottom - top
    scale = min(ART_WIDTH / crop_width, ART_HEIGHT / crop_height)
    output_width = max(1, round(crop_width * scale))
    output_height = max(1, round(crop_height * scale))
    offset_x = (SPRITE_WIDTH - output_width) // 2
    offset_y = (SPRITE_HEIGHT - output_height) // 2
    output = [[0] * SPRITE_WIDTH for _ in range(SPRITE_HEIGHT)]
    for target_y in range(output_height):
        source_top = top + target_y * crop_height // output_height
        source_bottom = max(
            source_top + 1,
            top + (target_y + 1) * crop_height // output_height,
        )
        for target_x in range(output_width):
            source_left = left + target_x * crop_width // output_width
            source_right = max(
                source_left + 1,
                left + (target_x + 1) * crop_width // output_width,
            )
            sample_count = (source_right - source_left) * (
                source_bottom - source_top
            )
            foreground_count = sum(
                mask[source_y * width + source_x]
                for source_y in range(source_top, source_bottom)
                for source_x in range(source_left, source_right)
            )
            output[offset_y + target_y][offset_x + target_x] = int(
                foreground_count / sample_count >= FOREGROUND_COVERAGE
            )
    return output


def encode_sprite(pixels: list[list[int]]) -> bytes:
    output = bytearray()
    for row in pixels:
        for byte_column in range(3):
            value = 0
            for bit in range(8):
                value = (value << 1) | row[byte_column * 8 + bit]
            output.append(value)
    output.append(0)
    return bytes(output)


def write_asm(path: Path, address: int, label: str, description: str, data: bytes):
    lines = [
        "; Generated by scripts/build-side-control-icons.py; do not edit.",
        f"; {description}",
        f"* = ${address:04x}",
        f"{label}:",
    ]
    for start in range(0, len(data), 8):
        values = ",".join(f"${value:02x}" for value in data[start : start + 8])
        lines.append(f"!byte {values}")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_preview(path: Path, pixels: list[list[int]]):
    with path.open("wb") as preview:
        preview.write(
            f"P6\n{SPRITE_WIDTH * PREVIEW_SCALE} "
            f"{SPRITE_HEIGHT * PREVIEW_SCALE}\n255\n".encode("ascii")
        )
        for row in pixels:
            scanline = b"".join(
                bytes(PREVIEW_COLOR if value else (0, 0, 0)) * PREVIEW_SCALE
                for value in row
            )
            for _ in range(PREVIEW_SCALE):
                preview.write(scanline)


def convert(
    source: Path,
    output_directory: Path,
    basename: str,
    address: int,
    label: str,
    description: str,
    component_count: int,
):
    width, height = dimensions(source)
    mask = light_green_mask(raw_rgb(source), width, height)
    pictogram = select_pictogram(mask, width, height, component_count)
    pixels = resize_to_sprite(pictogram, width)
    write_asm(
        output_directory / f"{basename}.asm", address, label, description,
        encode_sprite(pixels),
    )
    write_preview(output_directory / f"{basename}_preview.ppm", pixels)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: build-side-control-icons.py "
            "NEW_GAME_MASTER.png OUTPUT_DIRECTORY"
        )
    output_directory = Path(sys.argv[2])
    output_directory.mkdir(parents=True, exist_ok=True)
    convert(
        Path(sys.argv[1]), output_directory, "new_game", 0x5D80,
        "NewGameSprite",
        "Overlapping-dice New Game icon derived from the supplied badge.", 2,
    )
    print("Created 24x21 New Game hi-res sprite")


if __name__ == "__main__":
    main()
