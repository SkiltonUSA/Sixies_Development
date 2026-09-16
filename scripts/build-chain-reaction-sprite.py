#!/usr/bin/env python3

"""Build the Chain Reaction bitmap panel used by the merge-callout renderer."""

import pathlib
import struct
import subprocess
import sys


EXPECTED_SOURCE_SIZE = (77, 39)
PANEL_WIDTH = 72
PANEL_HEIGHT = 64
PANEL_BYTES_PER_ROW = PANEL_WIDTH // 8
PACKED_DATA_LIMIT = 224
SOURCE_ART_WIDTH = 64
SOURCE_ART_HEIGHT = 32
GREEN_CHANNEL_MARGIN = 6


def load_source_mask(path):
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG image")
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != EXPECTED_SOURCE_SIZE:
        raise ValueError(
            f"chain-reaction master must be {EXPECTED_SOURCE_SIZE[0]}x"
            f"{EXPECTED_SOURCE_SIZE[1]}, got {width}x{height}"
        )
    rgb = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    if len(rgb) != width * height * 3:
        raise ValueError(f"could not decode all pixels from {path}")

    mask = bytearray(width * height)
    for pixel in range(width * height):
        offset = pixel * 3
        red, green, blue = rgb[offset:offset + 3]
        # Convert the supplied pale-green callout to white. Its black outline
        # and original lettering remain transparent against the panel's black
        # background, preserving the source image instead of redrawing it.
        mask[pixel] = (
            green >= red + GREEN_CHANNEL_MARGIN
            and green >= blue + GREEN_CHANNEL_MARGIN
        )
    return mask, width, height


def build_panel(mask, width, height):
    """Scale the attachment's original filled callout into the bitmap panel."""
    panel = bytearray(PANEL_WIDTH * PANEL_HEIGHT // 8)
    left = (PANEL_WIDTH - SOURCE_ART_WIDTH) // 2
    top = (PANEL_HEIGHT - SOURCE_ART_HEIGHT) // 2

    for target_y in range(SOURCE_ART_HEIGHT):
        source_y0 = target_y * height // SOURCE_ART_HEIGHT
        source_y1 = (target_y + 1) * height // SOURCE_ART_HEIGHT
        for target_x in range(SOURCE_ART_WIDTH):
            source_x0 = target_x * width // SOURCE_ART_WIDTH
            source_x1 = (target_x + 1) * width // SOURCE_ART_WIDTH
            samples = 0
            dark_samples = 0
            for source_y in range(source_y0, max(source_y0 + 1, source_y1)):
                for source_x in range(source_x0, max(source_x0 + 1, source_x1)):
                    samples += 1
                    dark_samples += mask[source_y * width + source_x]
            if dark_samples * 3 < samples:
                continue
            x = left + target_x
            y = top + target_y
            offset = ((y // 8) * PANEL_BYTES_PER_ROW + (x // 8)) * 8 + (y % 8)
            panel[offset] |= 0x80 >> (x & 7)
    return panel


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


def write_preview(panel, destination):
    preview = bytearray(PANEL_WIDTH * PANEL_HEIGHT * 3)
    for y in range(PANEL_HEIGHT):
        for x in range(PANEL_WIDTH):
            offset = ((y // 8) * PANEL_BYTES_PER_ROW + (x // 8)) * 8 + (y % 8)
            color = 255 if panel[offset] & (0x80 >> (x & 7)) else 0
            pixel = (y * PANEL_WIDTH + x) * 3
            preview[pixel:pixel + 3] = bytes((color, color, color))
    destination.write_bytes(
        f"P6\n{PANEL_WIDTH} {PANEL_HEIGHT}\n255\n".encode("ascii") + preview
    )


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-chain-reaction-sprite.py SOURCE_PNG OUTPUT_DIRECTORY")
    source = pathlib.Path(sys.argv[1])
    output_directory = pathlib.Path(sys.argv[2])
    output_directory.mkdir(parents=True, exist_ok=True)

    mask, width, height = load_source_mask(source)
    panel = build_panel(mask, width, height)
    packed = pack(panel)
    if len(packed) > PACKED_DATA_LIMIT:
        raise ValueError(
            f"packed Chain Reaction panel is {len(packed)} bytes; "
            f"the fixed slot permits {PACKED_DATA_LIMIT}"
        )
    (output_directory / "chain_reaction_sprite.bin").write_bytes(packed)
    write_preview(panel, output_directory / "chain_reaction_preview.ppm")
    print(
        f"Built 72x64 Chain Reaction bitmap callout "
        f"({len(packed)} packed bytes)"
    )


if __name__ == "__main__":
    main()
