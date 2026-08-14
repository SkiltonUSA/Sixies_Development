#!/usr/bin/env python3

"""Build compact hi-res sidebar callouts from edited PNG artwork."""

import pathlib
import struct
import subprocess
import sys


SOURCE_NAMES = (
    "AWESOME",
    "BOOM",
    "DANG",
    "LETS_GO",
    "WHOA",
    "WOW",
    "YEAH",
    "YES",
    "FIVES",
    "SIXIES",
)
GENERAL_CALLOUT_COUNT = 8
FIVES_INDEX = 8
SIXIES_INDEX = 9
PANEL_WIDTH = 80
PANEL_HEIGHT = 80
PANEL_BYTES_PER_ROW = PANEL_WIDTH // 8
DATA_ADDRESS = 0x3000


def load_png_mask(path):
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG image")
    width, height = struct.unpack(">II", header[16:24])
    rgb = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    if len(rgb) != width * height * 3:
        raise ValueError(f"could not decode all pixels from {path}")

    # Keep the white artwork and purple keyline while dropping the black
    # background and faint screenshot compression noise.
    mask = bytearray(width * height)
    for pixel in range(width * height):
        offset = pixel * 3
        mask[pixel] = max(rgb[offset:offset + 3]) >= 64
    return mask, width, height


def source_pixel(mask, width, x, y):
    return bool(mask[y * width + x])


def bounds(mask, width, height):
    pixels = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if source_pixel(mask, width, x, y)
    ]
    if not pixels:
        raise ValueError("callout artwork is empty")
    return (
        min(x for x, _ in pixels),
        min(y for _, y in pixels),
        max(x for x, _ in pixels),
        max(y for _, y in pixels),
    )


def build_panel(mask, width, height):
    left, top, right, bottom = bounds(mask, width, height)
    source_width = right - left + 1
    source_height = bottom - top + 1
    scale = min(PANEL_WIDTH / source_width, PANEL_HEIGHT / source_height)
    target_width = max(1, round(source_width * scale))
    target_height = max(1, round(source_height * scale))
    offset_x = (PANEL_WIDTH - target_width) // 2
    offset_y = (PANEL_HEIGHT - target_height) // 2
    output = bytearray(PANEL_WIDTH * PANEL_HEIGHT // 8)

    for target_y in range(target_height):
        source_y0 = top + (target_y * source_height) // target_height
        source_y1 = top + ((target_y + 1) * source_height) // target_height
        for target_x in range(target_width):
            source_x0 = left + (target_x * source_width) // target_width
            source_x1 = left + ((target_x + 1) * source_width) // target_width

            # Keep a source pixel only when it covers a meaningful part of the
            # target cell. Point sampling was breaking narrow letter strokes.
            samples = 0
            set_samples = 0
            for source_y in range(source_y0, max(source_y0 + 1, source_y1)):
                for source_x in range(source_x0, max(source_x0 + 1, source_x1)):
                    samples += 1
                    set_samples += source_pixel(mask, width, source_x, source_y)
            if set_samples * 3 < samples:
                continue
            x = target_x + offset_x
            y = target_y + offset_y
            offset = ((y // 8) * PANEL_BYTES_PER_ROW + (x // 8)) * 8 + (y % 8)
            output[offset] |= 0x80 >> (x & 7)
    return output


def pack(data):
    output = bytearray()
    index = 0
    while index < len(data):
        run = 1
        while index + run < len(data) and data[index + run] == data[index] and run < 127:
            run += 1
        if run >= 3:
            output.extend((0x80 | run, data[index]))
            index += run
            continue

        literal_start = index
        index += run
        while index < len(data) and index - literal_start < 127:
            next_run = 1
            while (
                index + next_run < len(data)
                and data[index + next_run] == data[index]
                and next_run < 127
            ):
                next_run += 1
            if next_run >= 3:
                break
            index += next_run
        literal = data[literal_start:index]
        output.append(len(literal))
        output.extend(literal)
    output.append(0)
    return output


def write_preview(panels, destination):
    columns = 3
    rows = (len(panels) + columns - 1) // columns
    width = PANEL_WIDTH * columns
    height = PANEL_HEIGHT * rows
    preview = bytearray(width * height * 3)
    for panel_index, panel in enumerate(panels):
        origin_x = (panel_index % columns) * PANEL_WIDTH
        origin_y = (panel_index // columns) * PANEL_HEIGHT
        for y in range(PANEL_HEIGHT):
            for x in range(PANEL_WIDTH):
                offset = ((y // 8) * PANEL_BYTES_PER_ROW + (x // 8)) * 8 + (y % 8)
                color = 255 if panel[offset] & (0x80 >> (x & 7)) else 0
                pixel = ((origin_y + y) * width + origin_x + x) * 3
                preview[pixel:pixel + 3] = bytes((color, color, color))
    destination.write_bytes(f"P6\n{width} {height}\n255\n".encode("ascii") + preview)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-merge-callouts.py SOURCE_DIRECTORY OUTPUT_DIRECTORY")
    source_directory = pathlib.Path(sys.argv[1])
    output_directory = pathlib.Path(sys.argv[2])
    output_directory.mkdir(parents=True, exist_ok=True)

    panels = []
    packed = bytearray()
    offsets = []
    for name in SOURCE_NAMES:
        mask, width, height = load_png_mask(source_directory / f"{name}.png")
        panel = build_panel(mask, width, height)
        offsets.append(len(packed))
        packed.extend(pack(panel))
        panels.append(panel)

    (output_directory / "merge_callouts_packed.bin").write_bytes(packed)
    (output_directory / "merge_callout_data.asm").write_text(
        "; Generated by scripts/build-merge-callouts.py.\n"
        f"* = ${DATA_ADDRESS:04x}\n"
        "MergeCalloutPackedData:\n"
        "!bin \"src/assets/merge_callouts_packed.bin\"\n"
        "MergeCalloutOffsetLo: !byte " + ",".join(f"${offset & 0xff:02x}" for offset in offsets) + "\n"
        "MergeCalloutOffsetHi: !byte " + ",".join(f"${offset >> 8:02x}" for offset in offsets) + "\n"
        f"MergeCalloutGeneralCount = {GENERAL_CALLOUT_COUNT}\n"
        f"MergeCalloutFivesIndex = {FIVES_INDEX}\n"
        f"MergeCalloutSixiesIndex = {SIXIES_INDEX}\n"
    )
    write_preview(panels, output_directory / "merge_callouts_preview.ppm")
    print(f"Packed {len(panels)} mascot callouts into {len(packed)} bytes")


if __name__ == "__main__":
    main()
