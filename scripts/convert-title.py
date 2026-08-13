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
    "A": (0x18, 0x3C, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00),
    "B": (0x7C, 0x66, 0x66, 0x7C, 0x66, 0x66, 0x7C, 0x00),
    "C": (0x3C, 0x66, 0x60, 0x60, 0x60, 0x66, 0x3C, 0x00),
    "D": (0x78, 0x6C, 0x66, 0x66, 0x66, 0x6C, 0x78, 0x00),
    "E": (0x7E, 0x60, 0x60, 0x78, 0x60, 0x60, 0x7E, 0x00),
    "F": (0x7E, 0x60, 0x60, 0x78, 0x60, 0x60, 0x60, 0x00),
    "G": (0x3C, 0x66, 0x60, 0x6E, 0x66, 0x66, 0x3C, 0x00),
    "H": (0x66, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00),
    "I": (0x3C, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00),
    "J": (0x1E, 0x0C, 0x0C, 0x0C, 0x0C, 0x6C, 0x38, 0x00),
    "K": (0x66, 0x6C, 0x78, 0x70, 0x78, 0x6C, 0x66, 0x00),
    "L": (0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7E, 0x00),
    "M": (0x63, 0x77, 0x7F, 0x6B, 0x63, 0x63, 0x63, 0x00),
    "N": (0x66, 0x76, 0x7E, 0x7E, 0x6E, 0x66, 0x66, 0x00),
    "O": (0x3C, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00),
    "P": (0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60, 0x60, 0x00),
    "Q": (0x3C, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x0E, 0x00),
    "R": (0x7C, 0x66, 0x66, 0x7C, 0x78, 0x6C, 0x66, 0x00),
    "S": (0x3C, 0x66, 0x60, 0x3C, 0x06, 0x66, 0x3C, 0x00),
    "T": (0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00),
    "U": (0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00),
    "V": (0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00),
    "W": (0x63, 0x63, 0x63, 0x6B, 0x7F, 0x77, 0x63, 0x00),
    "X": (0x66, 0x66, 0x3C, 0x18, 0x3C, 0x66, 0x66, 0x00),
    "Y": (0x66, 0x66, 0x66, 0x3C, 0x18, 0x18, 0x18, 0x00),
    "Z": (0x7E, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x00),
    "0": (0x3C, 0x66, 0x6E, 0x76, 0x66, 0x66, 0x3C, 0x00),
    "1": (0x18, 0x18, 0x38, 0x18, 0x18, 0x18, 0x7E, 0x00),
    "2": (0x3C, 0x66, 0x06, 0x0C, 0x30, 0x60, 0x7E, 0x00),
    "3": (0x3C, 0x66, 0x06, 0x1C, 0x06, 0x66, 0x3C, 0x00),
    "4": (0x06, 0x0E, 0x1E, 0x66, 0x7F, 0x06, 0x06, 0x00),
    "5": (0x7E, 0x60, 0x7C, 0x06, 0x06, 0x66, 0x3C, 0x00),
    "6": (0x3C, 0x66, 0x60, 0x7C, 0x66, 0x66, 0x3C, 0x00),
    "7": (0x7E, 0x66, 0x0C, 0x18, 0x18, 0x18, 0x18, 0x00),
    "8": (0x3C, 0x66, 0x66, 0x3C, 0x66, 0x66, 0x3C, 0x00),
    "9": (0x3C, 0x66, 0x66, 0x3E, 0x06, 0x66, 0x3C, 0x00),
    " ": (0, 0, 0, 0, 0, 0, 0, 0),
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


def clear_bitmap_prompt(rgb):
    for y in range(176, HEIGHT):
        start = (y * WIDTH + 80) * 3
        rgb[start:(y * WIDTH + 240) * 3] = bytes(160 * 3)


CHARSET_FIRST = 0x20
CHARSET_COUNT = 64
TITLE_BACKGROUND = 0


def load_sixies_font(output):
    charset_path = output / "font/SixiesFont_charset.bin"
    charset = charset_path.read_bytes()
    expected = CHARSET_COUNT * 8
    if len(charset) != expected:
        raise ValueError(f"expected {expected} bytes in {charset_path}, received {len(charset)}")

    def glyph(character):
        index = ord(character) - CHARSET_FIRST
        return tuple(charset[index * 8:(index + 1) * 8])

    return {
        character: glyph(character)
        for character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
    }


def title_prompt_sprites(font):
    text = "PRESS FIRE START"
    rows = []
    for y in range(8):
        bits = [False] * 8
        for character in text:
            value = font[character][y]
            bits.extend(bool(value & (1 << (7 - x))) for x in range(8))
        bits.extend([False] * 8)
        rows.append(bits)

    sprites = bytearray()
    for sprite in range(6):
        for y in range(21):
            value = 0
            source = rows[y][sprite * 24:(sprite + 1) * 24] if y < 8 else [False] * 24
            for bit in source:
                value = (value << 1) | int(bit)
            sprites.extend((value >> 16, (value >> 8) & 0xff, value & 0xff))
        sprites.append(0)
    return sprites


def draw_prompt_preview(preview, font):
    text = "PRESS FIRE START"
    start_x = 96
    start_y = 184
    for index, character in enumerate(text):
        for y, value in enumerate(font[character]):
            for x in range(8):
                if value & (1 << (7 - x)):
                    offset = ((start_y + y) * WIDTH + start_x + index * 8 + x) * 3
                    preview[offset:offset + 3] = bytes(PALETTE[1])


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
    font = load_sixies_font(output)
    rgb = decode_png(source)
    clear_bitmap_prompt(rgb)
    bitmap, screen, color_ram, preview = encode(rgb)
    draw_prompt_preview(preview, font)
    (output / "title_bitmap.bin").write_bytes(bitmap)
    (output / "title_screen.bin").write_bytes(screen)
    (output / "title_color.bin").write_bytes(color_ram)
    (output / "title_prompt_sprites.bin").write_bytes(title_prompt_sprites(font))
    # A standard Koala export so scripts/pack-koala.py can compress the title
    # the same way it compresses the Game Over image. The title screen runs on
    # a black background.
    (output / "title.kla").write_bytes(
        bytes((0x00, 0x60)) + bitmap + screen + color_ram + bytes((TITLE_BACKGROUND,))
    )
    with (output / "title_preview.ppm").open("wb") as file:
        file.write(f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii"))
        file.write(preview)


if __name__ == "__main__":
    main()
