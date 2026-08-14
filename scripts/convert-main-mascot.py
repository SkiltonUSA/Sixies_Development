#!/usr/bin/env python3

import collections
import itertools
import pathlib
import subprocess
import sys


WIDTH = 80
HEIGHT = 80
USE_FULL_PALETTE = False
USE_SOLID_LOGO_PALETTE = False
FORCE_BLACK_BACKGROUND = False
PREFER_MASCOT_DETAILS = False
MASCOT_BLACK_WHITE_CELLS = {
    # Eye/pupil and mouth cells need black contrast to retain the expression.
    (3, 4), (3, 5),
}
MASCOT_PURPLE_BLACK_CELLS = {
    # The mouth shares cells with the purple face. Keep that base color and
    # the black smile; a red tongue would make this a third color.
    (4, 4), (4, 5),
}
MASCOT_SHOE_CELLS = {
    (7, 0), (7, 1), (7, 2), (7, 3), (7, 6), (7, 7), (7, 8), (7, 9),
    *( (row, column) for row in (8, 9) for column in range(10) ),
}
MASCOT_FOOT_GAP_CELLS = {(7, 4), (7, 5)}
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


def koala_rgb(path):
    data = pathlib.Path(path).read_bytes()
    if len(data) != 10003 or data[:2] != b"\x00\x60":
        raise ValueError("expected a 10003-byte Koala image loaded at $6000")

    bitmap = data[2:8002]
    screen = data[8002:9002]
    color_ram = data[9002:10002]
    background = data[10002] & 0x0F
    output = bytearray()
    for y in range(200):
        cell_y, bitmap_line = divmod(y, 8)
        for cell_x in range(40):
            cell = cell_y * 40 + cell_x
            colors = (
                background,
                screen[cell] >> 4,
                screen[cell] & 0x0F,
                color_ram[cell] & 0x0F,
            )
            byte = bitmap[cell_y * 320 + cell_x * 8 + bitmap_line]
            for shift in (6, 4, 2, 0):
                output.extend(PALETTE[colors[(byte >> shift) & 3]])
                output.extend(PALETTE[colors[(byte >> shift) & 3]])
    return output


def fit_koala_rgb(rgb, left, top, crop_width, crop_height):
    target_width = WIDTH - 4
    target_height = HEIGHT - 4
    scale = min(target_width / crop_width, target_height / crop_height)
    scaled_width = max(1, round(crop_width * scale))
    scaled_height = max(1, round(crop_height * scale))
    output = bytearray(WIDTH * HEIGHT * 3)
    offset_x = (WIDTH - scaled_width) // 2
    offset_y = (HEIGHT - scaled_height) // 2
    for target_y in range(scaled_height):
        source_y = top + min(crop_height - 1, int(target_y / scale))
        for target_x in range(scaled_width):
            source_x = left + min(crop_width - 1, int(target_x / scale))
            source = (source_y * 320 + source_x) * 3
            target = ((target_y + offset_y) * WIDTH + target_x + offset_x) * 3
            output[target:target + 3] = rgb[source:source + 3]
    return output


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
    if USE_SOLID_LOGO_PALETTE:
        return 0 if max(red, green, blue) < 48 else 13
    if USE_FULL_PALETTE:
        return min(
            range(len(PALETTE)),
            key=lambda color: sum(
                (channel - target) ** 2
                for channel, target in zip((red, green, blue), PALETTE[color])
            ),
        )
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
            if FORCE_BLACK_BACKGROUND:
                foreground_counts = [
                    (color, count) for color, count in counts.most_common()
                    if color != 0
                ]
                foreground = foreground_counts[0][0] if foreground_counts else 1
                pair = [0, foreground]
            elif PREFER_MASCOT_DETAILS and (cell_y, cell_x) in MASCOT_FOOT_GAP_CELLS:
                # Keep a clean black gap between the two shoes. The source's
                # antialiased purple bridge turns into a distracting block in
                # the hi-res reduction.
                pair = [0, 0]
            elif PREFER_MASCOT_DETAILS and (cell_y, cell_x) in MASCOT_SHOE_CELLS:
                # Shoes sit against the black background. Use their two
                # strongest high-contrast colors so purple cannot fill the
                # empty space between the feet.
                pair = [0, 1]
            elif PREFER_MASCOT_DETAILS and (cell_y, cell_x) in MASCOT_PURPLE_BLACK_CELLS:
                pair = [4, 0]
            elif PREFER_MASCOT_DETAILS and (cell_y, cell_x) in MASCOT_BLACK_WHITE_CELLS:
                pair = [0, 1]
            elif PREFER_MASCOT_DETAILS and 4 in counts:
                # Preserve the character's broad purple silhouette. In a
                # three-color source cell, selecting black and white punches
                # holes through the body because hi-res can show only a pair.
                # Purple plus white keeps its face, hands, and shoes readable.
                pair = [4, 1] if 1 in counts else [0, 4]
            else:
                palette = list(counts)
                if len(palette) == 1:
                    pair = [palette[0], palette[0]]
                else:
                    # A C64 hi-res character has just two colors. Favor white
                    # facial details over broad purple fills when all three
                    # mascot colors meet in the same cell.
                    def weight(color):
                        if PREFER_MASCOT_DETAILS and color == 1:
                            return 4
                        if PREFER_MASCOT_DETAILS and color == 0:
                            return 2
                        return 1

                    def pair_error(candidate):
                        return sum(
                            count * weight(color) * min(
                                sum((channel - target) ** 2 for channel, target in zip(PALETTE[color], PALETTE[choice]))
                                for choice in candidate
                            )
                            for color, count in counts.items()
                        )

                    pair = list(min(itertools.combinations(palette, 2), key=pair_error))
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
    global WIDTH, HEIGHT, USE_FULL_PALETTE
    global USE_SOLID_LOGO_PALETTE, FORCE_BLACK_BACKGROUND, PREFER_MASCOT_DETAILS
    if len(sys.argv) not in (3, 4, 6, 7):
        raise SystemExit(
            "usage: convert-main-mascot.py INPUT.png OUTPUT_DIRECTORY "
            "[PREFIX [WIDTH HEIGHT [full-palette|solid-logo]]]"
        )
    source = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    prefix = sys.argv[3] if len(sys.argv) == 4 else "main_mascot"
    if len(sys.argv) >= 6:
        prefix = sys.argv[3]
        WIDTH = int(sys.argv[4])
        HEIGHT = int(sys.argv[5])
    palette_mode = sys.argv[6] if len(sys.argv) == 7 else ""
    USE_FULL_PALETTE = palette_mode == "full-palette"
    USE_SOLID_LOGO_PALETTE = palette_mode == "solid-logo"
    FORCE_BLACK_BACKGROUND = palette_mode == "solid-logo"
    PREFER_MASCOT_DETAILS = prefix == "main_mascot"
    if WIDTH % 8 or HEIGHT % 8:
        raise SystemExit("mascot width and height must be multiples of 8")
    is_koala = source.suffix.lower() == ".kla"
    width, height = (320, 200) if is_koala else dimensions(source)
    source_rgb = koala_rgb(source) if is_koala else raw_rgb(source)
    left, top, crop_width, crop_height = content_bounds(source_rgb, width, height)
    if is_koala:
        fitted = fit_koala_rgb(source_rgb, left, top, crop_width, crop_height)
    else:
        fitted = raw_rgb(source, (
            f"crop={crop_width}:{crop_height}:{left}:{top},"
            f"scale={WIDTH - 4}:{HEIGHT - 4}:"
            "force_original_aspect_ratio=decrease:flags=neighbor,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
        ))
    bitmap, screen, preview = encode(fitted)
    output.mkdir(parents=True, exist_ok=True)
    (output / f"{prefix}_bitmap.bin").write_bytes(bitmap)
    (output / f"{prefix}_screen.bin").write_bytes(screen)
    with (output / f"{prefix}_preview.ppm").open("wb") as file:
        file.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        file.write(preview)
    print(f"Created {len(bitmap)} bitmap bytes and {len(screen)} screen bytes")


if __name__ == "__main__":
    main()
