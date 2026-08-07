#!/usr/bin/env python3

import collections
import pathlib
import subprocess
import sys


WIDTH = 64
HEIGHT = 80
PALETTE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
]


def dimensions(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path),
    ]).decode("ascii").strip()
    return tuple(int(value) for value in result.split("x"))


def raw_rgb(path, video_filter=None):
    command = ["ffmpeg", "-v", "error", "-i", str(path)]
    if video_filter:
        command.extend(("-vf", video_filter))
    command.extend(("-f", "rawvideo", "-pix_fmt", "rgb24", "-"))
    return subprocess.check_output(command)


def content_bounds(rgb, width, height):
    points = []
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 3
            if max(rgb[offset:offset + 3]) > 42:
                points.append((x, y))
    left = max(0, min(x for x, _ in points) - 4)
    top = max(0, min(y for _, y in points) - 4)
    right = min(width, max(x for x, _ in points) + 5)
    bottom = min(height, max(y for _, y in points) + 5)
    return left, top, right - left, bottom - top


def flat_color(red, green, blue):
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    if maximum < 42:
        return 0
    if maximum - minimum < 52:
        return 1 if maximum > 96 else 0
    if red > green * 1.55 and red > blue * 1.30:
        return 2
    return 4


def encode(rgb):
    pixels = []
    for offset in range(0, len(rgb), 3):
        pixels.append(flat_color(*rgb[offset:offset + 3]))

    bitmap = bytearray()
    screen = bytearray()
    preview = bytearray(WIDTH * HEIGHT * 3)
    for cell_y in range(HEIGHT // 8):
        for cell_x in range(WIDTH // 8):
            colors = [
                pixels[(cell_y * 8 + y) * WIDTH + cell_x * 8 + x]
                for y in range(8) for x in range(8)
            ]
            counts = collections.Counter(colors)
            pair = [color for color, _ in counts.most_common(2)]
            pair.extend([0] * (2 - len(pair)))
            if cell_y == 0 and cell_x == 4:
                pair = [0, 4]
            background, foreground = pair
            screen.append((foreground << 4) | background)

            for y in range(8):
                encoded = 0
                for x in range(8):
                    source = pixels[(cell_y * 8 + y) * WIDTH + cell_x * 8 + x]
                    bit = min(
                        range(2),
                        key=lambda item: sum(
                            (channel - target) ** 2
                            for channel, target in zip(PALETTE[source], PALETTE[pair[item]])
                        ),
                    )
                    encoded = (encoded << 1) | bit
                    output = PALETTE[pair[bit]]
                    target = ((cell_y * 8 + y) * WIDTH + cell_x * 8 + x) * 3
                    preview[target:target + 3] = bytes(output)
                bitmap.append(encoded)
    return bitmap, screen, preview


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: convert-main-mascot.py INPUT.png OUTPUT_DIRECTORY")
    source = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    width, height = dimensions(source)
    source_rgb = raw_rgb(source)
    left, top, crop_width, crop_height = content_bounds(source_rgb, width, height)
    fitted = raw_rgb(source, (
        f"crop={crop_width}:{crop_height}:{left}:{top},"
        "scale=60:76:force_original_aspect_ratio=decrease:flags=neighbor,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
    ))
    bitmap, screen, preview = encode(fitted)
    output.mkdir(parents=True, exist_ok=True)
    (output / "main_mascot_bitmap.bin").write_bytes(bitmap)
    (output / "main_mascot_screen.bin").write_bytes(screen)
    with (output / "main_mascot_preview.ppm").open("wb") as file:
        file.write(b"P6\n64 80\n255\n")
        file.write(preview)
    print(f"Created {len(bitmap)} bitmap bytes and {len(screen)} screen bytes")


if __name__ == "__main__":
    main()
