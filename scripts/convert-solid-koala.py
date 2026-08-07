#!/usr/bin/env python3

import collections
import pathlib
import subprocess
import sys


WIDTH = 320
HEIGHT = 200
LOGICAL_WIDTH = 160
PALETTE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
]


def decode_and_fit(path, stretch_logo=False):
    if stretch_logo:
        video_filter = (
            "scale=300:250:flags=neighbor,"
            "crop=300:200:0:18,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
        )
    else:
        video_filter = (
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease:flags=neighbor,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
        )
    command = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", video_filter,
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    data = subprocess.check_output(command)
    if len(data) != WIDTH * HEIGHT * 3:
        raise ValueError("failed to create a 320x200 RGB frame")
    return data


def flat_color(red, green, blue):
    maximum = max(red, green, blue)
    minimum = min(red, green, blue)
    spread = maximum - minimum
    if maximum < 38:
        return 0
    if spread < 34:
        if maximum >= 112:
            return 1
        return 11
    if green > red * 1.12 and green > blue * 1.18:
        return 13
    if blue > red * 1.18 and blue > green * 1.12:
        return 6
    if red >= green and red >= blue:
        if blue > red * 0.62:
            return 4
        if blue > green * 0.75 and blue > red * 0.32:
            return 10
        if green > red * 0.68:
            return 7
        if green > red * 0.28:
            return 8
        return 10
    if blue > green * 1.12 and red > green * 1.20:
        return 4
    return min(
        (1, 4, 6, 7, 8, 10, 11, 13),
        key=lambda color: sum(
            (channel - target) ** 2
            for channel, target in zip((red, green, blue), PALETTE[color])
        ),
    )


def classify(rgb):
    logical = []
    for y in range(HEIGHT):
        row = []
        for x in range(0, WIDTH, 2):
            offset = (y * WIDTH + x) * 3
            pair = rgb[offset:offset + 6]
            average = tuple((pair[channel] + pair[channel + 3]) // 2 for channel in range(3))
            color = flat_color(*average)
            if color == 6 and 42 <= x // 2 < 68 and 35 <= y < 160:
                color = 4
            row.append(color)
        logical.append(row)
    return logical


def encode(logical):
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
            counts = collections.Counter(color for color in colors if color)
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
                        key=lambda item: sum(
                            (channel - target) ** 2
                            for channel, target in zip(PALETTE[source_color], PALETTE[choices[item]])
                        ),
                    )
                    encoded = (encoded << 2) | code
                    output = PALETTE[choices[code]]
                    pixel_x = (cell_x * 4 + x) * 2
                    pixel_y = cell_y * 8 + y
                    for doubled_x in (pixel_x, pixel_x + 1):
                        offset = (pixel_y * WIDTH + doubled_x) * 3
                        preview[offset:offset + 3] = bytes(output)
                bitmap.append(encoded)
    return bitmap, screen, color_ram, preview


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: convert-solid-koala.py INPUT.png OUTPUT_DIRECTORY BASENAME")
    source = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    basename = sys.argv[3]
    output.mkdir(parents=True, exist_ok=True)
    bitmap, screen, color_ram, preview = encode(classify(
        decode_and_fit(source, stretch_logo=basename == "game_over_koala")
    ))
    koala = bytes((0x00, 0x60)) + bitmap + screen + color_ram + bytes((0,))
    (output / f"{basename}.kla").write_bytes(koala)
    (output / f"{basename}_bitmap.bin").write_bytes(bitmap)
    (output / f"{basename}_screen.bin").write_bytes(screen)
    (output / f"{basename}_color.bin").write_bytes(color_ram)
    with (output / f"{basename}_preview.ppm").open("wb") as file:
        file.write(b"P6\n320 200\n255\n")
        file.write(preview)
    print(f"Created solid-color Koala image: {len(koala)} bytes")


if __name__ == "__main__":
    main()
