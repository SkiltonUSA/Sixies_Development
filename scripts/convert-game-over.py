#!/usr/bin/env python3

import pathlib
import subprocess
import sys


SOURCE_LIMIT = 160
PALETTE = [
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
]


def distance(left, right):
    return sum((a - b) * (a - b) for a, b in zip(left, right))


def dimensions(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(path),
    ]).decode("ascii").strip()
    return tuple(int(value) for value in result.split("x"))


def raw_rgb(path, video_filter=None):
    command = ["ffmpeg", "-v", "error", "-i", str(path)]
    if video_filter:
        command.extend(["-vf", video_filter])
    command.extend(["-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    return bytearray(subprocess.check_output(command))


def content_bounds(rgb, width, height):
    points = []
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 3
            if max(rgb[offset:offset + 3]) > 28:
                points.append((x, y))
    if not points:
        return 0, 0, width, height
    left = max(0, min(x for x, _ in points) - 8)
    top = max(0, min(y for _, y in points) - 8)
    right = min(width, max(x for x, _ in points) + 9)
    bottom = min(height, max(y for _, y in points) + 9)
    return left, top, right - left, bottom - top


def encode_hires(rgb):
    bitmap = bytearray()
    screen = bytearray()
    preview = bytearray(SOURCE_LIMIT * SOURCE_LIMIT * 3)
    for cell_y in range(20):
        for cell_x in range(20):
            pixels = [
                tuple(rgb[((cell_y * 8 + y) * SOURCE_LIMIT + cell_x * 8 + x) * 3:
                          ((cell_y * 8 + y) * SOURCE_LIMIT + cell_x * 8 + x) * 3 + 3])
                for y in range(8) for x in range(8)
            ]
            best_pair = min(
                ((background, foreground) for background in range(16) for foreground in range(16)),
                key=lambda pair: sum(
                    min(
                        distance(color, PALETTE[pair[0]]),
                        distance(color, PALETTE[pair[1]]),
                    )
                    for color in pixels
                ),
            )
            background, foreground = best_pair
            screen.append((foreground << 4) | background)

            working = [[list(map(float, pixels[y * 8 + x])) for x in range(8)] for y in range(8)]
            bits = [[0] * 8 for _ in range(8)]
            for y in range(8):
                left_to_right = (y & 1) == 0
                columns = range(8) if left_to_right else range(7, -1, -1)
                for x in columns:
                    corrected = tuple(max(0, min(255, value)) for value in working[y][x])
                    foreground_distance = distance(corrected, PALETTE[foreground])
                    background_distance = distance(corrected, PALETTE[background])
                    bit = int(foreground_distance < background_distance)
                    bits[y][x] = bit
                    output = PALETTE[foreground if bit else background]
                    error = [working[y][x][channel] - output[channel] for channel in range(3)]
                    direction = 1 if left_to_right else -1
                    neighbors = (
                        (x + direction, y, 7 / 16),
                        (x - direction, y + 1, 3 / 16),
                        (x, y + 1, 5 / 16),
                        (x + direction, y + 1, 1 / 16),
                    )
                    for neighbor_x, neighbor_y, weight in neighbors:
                        if 0 <= neighbor_x < 8 and neighbor_y < 8:
                            for channel in range(3):
                                working[neighbor_y][neighbor_x][channel] += error[channel] * weight

            for y in range(8):
                encoded = 0
                for x in range(8):
                    pixel_index = (cell_y * 8 + y) * SOURCE_LIMIT + cell_x * 8 + x
                    bit = bits[y][x]
                    encoded = (encoded << 1) | bit
                    output = PALETTE[foreground if bit else background]
                    preview[pixel_index * 3:pixel_index * 3 + 3] = bytes(output)
                bitmap.append(encoded)
    return bitmap, screen, preview


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: convert-game-over.py INPUT.png OUTPUT_DIRECTORY")
    source = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    width, height = dimensions(source)
    source_rgb = raw_rgb(source)
    left, top, crop_width, crop_height = content_bounds(source_rgb, width, height)
    video_filter = (
        f"crop={crop_width}:{crop_height}:{left}:{top},"
        "scale=156:156:force_original_aspect_ratio=decrease:flags=lanczos,"
        "pad=160:160:(ow-iw)/2:(oh-ih)/2:black"
    )
    fitted = raw_rgb(source, video_filter)
    bitmap, screen, preview = encode_hires(fitted)
    (output / "game_over_bitmap.bin").write_bytes(bitmap)
    (output / "game_over_screen.bin").write_bytes(screen)
    with (output / "game_over_preview.ppm").open("wb") as file:
        file.write(b"P6\n160 160\n255\n")
        file.write(preview)


if __name__ == "__main__":
    main()
