#!/usr/bin/env python3

"""Convert the supplied Sixies wordmark into the compact gameplay bitmap."""

from pathlib import Path
import subprocess
import sys


TARGET_WIDTH = 96
TARGET_HEIGHT = 16
BACKGROUND_CONTRAST = 48
FOREGROUND_COVERAGE = 0.15
MIN_COMPONENT_FRACTION = 0.07
BLACK = (0x00, 0x00, 0x00)
LIGHT_GREEN = (0xA9, 0xFF, 0x9F)


def dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x",
        str(path),
    ]).decode("ascii").strip()
    return tuple(int(value) for value in result.split("x"))


def raw_rgb(path: Path) -> bytes:
    return subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])


def foreground_mask(rgb: bytes, width: int, height: int) -> list[bool]:
    expected = width * height * 3
    if len(rgb) != expected:
        raise ValueError(f"expected {expected} RGB bytes, found {len(rgb)}")
    luminance = [
        sum(rgb[offset:offset + 3]) / 3
        for offset in range(0, len(rgb), 3)
    ]
    border = (
        luminance[:width]
        + luminance[-width:]
        + [luminance[row * width] for row in range(height)]
        + [luminance[row * width + width - 1] for row in range(height)]
    )
    background = sum(border) / len(border)
    if background < 128:
        return [value >= background + BACKGROUND_CONTRAST for value in luminance]
    return [value <= background - BACKGROUND_CONTRAST for value in luminance]


def filter_small_components(mask: list[bool], width: int, height: int) -> list[bool]:
    """Discard detached sparkles while retaining letters and dice-style dots."""
    seen = bytearray(width * height)
    components = []
    for start, value in enumerate(mask):
        if not value or seen[start]:
            continue
        seen[start] = 1
        pending = [start]
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
        components.append(members)
    if not components:
        return mask
    minimum_size = len(max(components, key=len)) * MIN_COMPONENT_FRACTION
    filtered = [False] * len(mask)
    for component in components:
        if len(component) >= minimum_size:
            for index in component:
                filtered[index] = True
    return filtered


def content_bounds(mask: list[bool], width: int, height: int) -> tuple[int, int, int, int]:
    points = [
        (index % width, index // width)
        for index, value in enumerate(mask)
        if value
    ]
    if not points:
        raise ValueError("gameplay logo contains no dark foreground artwork")
    return (
        min(x for x, _ in points),
        min(y for _, y in points),
        max(x for x, _ in points) + 1,
        max(y for _, y in points) + 1,
    )


def resize(mask: list[bool], width: int, height: int) -> list[list[int]]:
    left, top, right, bottom = content_bounds(mask, width, height)
    crop_width = right - left
    crop_height = bottom - top
    output = []
    for target_y in range(TARGET_HEIGHT):
        source_top = top + target_y * crop_height // TARGET_HEIGHT
        source_bottom = top + (target_y + 1) * crop_height // TARGET_HEIGHT
        source_bottom = max(source_top + 1, source_bottom)
        row = []
        for target_x in range(TARGET_WIDTH):
            source_left = left + target_x * crop_width // TARGET_WIDTH
            source_right = left + (target_x + 1) * crop_width // TARGET_WIDTH
            source_right = max(source_left + 1, source_right)
            sample_count = (source_right - source_left) * (source_bottom - source_top)
            foreground_count = sum(
                mask[source_y * width + source_x]
                for source_y in range(source_top, source_bottom)
                for source_x in range(source_left, source_right)
            )
            row.append(int(foreground_count / sample_count >= FOREGROUND_COVERAGE))
        output.append(row)
    return output


def encode_bitmap(pixels: list[list[int]]) -> bytes:
    output = bytearray()
    for cell_y in range(TARGET_HEIGHT // 8):
        for cell_x in range(TARGET_WIDTH // 8):
            for row in range(8):
                value = 0
                for column in range(8):
                    value = (value << 1) | pixels[cell_y * 8 + row][
                        cell_x * 8 + column
                    ]
                output.append(value)
    return bytes(output)


def encode_preview(pixels: list[list[int]]) -> bytes:
    output = bytearray()
    for row in pixels:
        for value in row:
            output.extend(LIGHT_GREEN if value else BLACK)
    return bytes(output)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: build-gameplay-logo.py GAMEPLAY_LOGO_MASTER.png OUTPUT_DIRECTORY"
        )
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    width, height = dimensions(source)
    mask = foreground_mask(raw_rgb(source), width, height)
    pixels = resize(filter_small_components(mask, width, height), width, height)
    output.mkdir(parents=True, exist_ok=True)
    (output / "gameplay_logo_bitmap.bin").write_bytes(encode_bitmap(pixels))
    with (output / "gameplay_logo_preview.ppm").open("wb") as preview:
        preview.write(f"P6\n{TARGET_WIDTH} {TARGET_HEIGHT}\n255\n".encode("ascii"))
        preview.write(encode_preview(pixels))
    print("Created 96x16 gameplay logo from the supplied wordmark")


if __name__ == "__main__":
    main()
