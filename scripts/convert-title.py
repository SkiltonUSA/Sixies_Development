#!/usr/bin/env python3

import collections
import pathlib
import subprocess
import sys


WIDTH = 320
HEIGHT = 200
PALETTE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
]
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "I": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x1F),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    " ": (0, 0, 0, 0, 0, 0, 0),
}


def distance(left, right):
    return sum((a - b) * (a - b) for a, b in zip(left, right))


def nearest_color(rgb, choices=range(16)):
    return min(choices, key=lambda index: distance(rgb, PALETTE[index]))


def decode_png(path):
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path),
    ]).decode("ascii").strip()
    source_width, source_height = (int(value) for value in probe.split("x"))
    if (source_width, source_height) == (160, 200):
        video_filter = f"scale={WIDTH}:{HEIGHT}:flags=neighbor"
    else:
        video_filter = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={WIDTH}:{HEIGHT}"
        )
    command = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", video_filter,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    data = subprocess.check_output(command)
    expected = WIDTH * HEIGHT * 3
    if len(data) != expected:
        raise ValueError(f"expected {expected} RGB bytes, received {len(data)}")
    return bytearray(data)


def draw_prompt(rgb):
    text = "PRESS FIRE"
    logical_width = len(text) * 6 - 1
    start_x = ((WIDTH // 2) - logical_width) & ~1
    start_y = 191
    end_x = start_x + logical_width * 2
    for y in range(188, HEIGHT):
        start = (y * WIDTH + start_x - 4) * 3
        rgb[start:(y * WIDTH + end_x + 4) * 3] = bytes((logical_width * 2 + 8) * 3)

    for char_index, character in enumerate(text):
        glyph = FONT[character]
        for glyph_y, bits in enumerate(glyph):
            for glyph_x in range(5):
                if not bits & (1 << (4 - glyph_x)):
                    continue
                x = start_x + ((char_index * 6 + glyph_x) * 2)
                y = start_y + glyph_y
                for pixel_x in (x, x + 1):
                    offset = (y * WIDTH + pixel_x) * 3
                    rgb[offset:offset + 3] = bytes(PALETTE[1])


def encode(rgb):
    logical = []
    for y in range(HEIGHT):
        row = []
        for x in range(0, WIDTH, 2):
            first = (y * WIDTH + x) * 3
            second = first + 3
            average = tuple((rgb[first + i] + rgb[second + i]) // 2 for i in range(3))
            row.append(nearest_color(average))
        logical.append(row)

    bitmap = bytearray()
    screen = bytearray()
    color_ram = bytearray()
    preview = bytearray(WIDTH * HEIGHT * 3)
    for cell_y in range(25):
        for cell_x in range(40):
            colors = [
                logical[cell_y * 8 + y][cell_x * 4 + x]
                for y in range(8) for x in range(4)
            ]
            counts = collections.Counter(color for color in colors if color != 0)
            local = [color for color, _ in counts.most_common(3)]
            local.extend([0] * (3 - len(local)))
            choices = [0] + local
            screen.append((local[0] << 4) | local[1])
            color_ram.append(local[2])

            for y in range(8):
                encoded = 0
                for x in range(4):
                    source_color = logical[cell_y * 8 + y][cell_x * 4 + x]
                    code = min(
                        range(4),
                        key=lambda item: distance(PALETTE[source_color], PALETTE[choices[item]]),
                    )
                    encoded = (encoded << 2) | code
                    output_color = PALETTE[choices[code]]
                    pixel_x = (cell_x * 4 + x) * 2
                    pixel_y = cell_y * 8 + y
                    for doubled_x in (pixel_x, pixel_x + 1):
                        offset = (pixel_y * WIDTH + doubled_x) * 3
                        preview[offset:offset + 3] = bytes(output_color)
                bitmap.append(encoded)
    return bitmap, screen, color_ram, preview


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: convert-title.py INPUT.png OUTPUT_DIRECTORY")
    source = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    rgb = decode_png(source)
    draw_prompt(rgb)
    bitmap, screen, color_ram, preview = encode(rgb)
    (output / "title_bitmap.bin").write_bytes(bitmap)
    (output / "title_screen.bin").write_bytes(screen)
    (output / "title_color.bin").write_bytes(color_ram)
    with (output / "title_preview.ppm").open("wb") as file:
        file.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        file.write(preview)


if __name__ == "__main__":
    main()
