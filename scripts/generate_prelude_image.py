#!/usr/bin/env python3
"""Generate the two-frame STAR / RETRODNA / WARS C64 hires prelude."""

from pathlib import Path
import math

from generate_logo import BAYER_4X4, decode_png, display_tone, sample_area
from generate_vader2 import PALETTE, color_error, write_rgb_png


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "assets" / "star_retro_war_vector_render.png"
EMBLEM_SOURCE = ROOT / "src" / "assets" / "imperial_emblem_vector_render.png"
ALT_TITLE_SOURCE = ROOT / "src" / "assets" / "a_retrodna_production_source.png"
PREVIEW_OUT = ROOT / "src" / "assets" / "star_retro_war_prelude_c64.png"
ALT_PREVIEW_OUT = ROOT / "src" / "assets" / "a_retrodna_production_prelude_c64.png"
BITMAP_OUT = ROOT / "src" / "generated" / "prelude_hires_bitmap.bin"
BITMAP_PRG_OUT = ROOT / "src" / "generated" / "prelude_hires_bitmap.prg"
COLOR_OUT = ROOT / "src" / "generated" / "prelude_hires_colors.bin"
COLOR_PRG_OUT = ROOT / "src" / "generated" / "prelude_hires_colors.prg"
ALT_BITMAP_OUT = ROOT / "src" / "generated" / "prelude_alt_hires_bitmap.bin"
ALT_BITMAP_PRG_OUT = ROOT / "src" / "generated" / "prelude_alt_hires_bitmap.prg"
ALT_COLOR_OUT = ROOT / "src" / "generated" / "prelude_alt_hires_colors.bin"
ALT_COLOR_PRG_OUT = ROOT / "src" / "generated" / "prelude_alt_hires_colors.prg"
ALT_COLOR_PACKED_OUT = (
    ROOT / "src" / "generated" / "prelude_alt_hires_colors_packed.bin"
)
ALT_COLOR_PACKED_PRG_OUT = (
    ROOT / "src" / "generated" / "prelude_alt_hires_colors_packed.prg"
)
ROTATION_INCLUDE_OUT = (
    ROOT / "src" / "generated" / "prelude_emblem_rotation.inc"
)

WIDTH = 320
HEIGHT = 200
INKS = (1, 6, 7, 8, 12, 14, 15)
VECTOR_CROP = (60, 55, 825, 525)
EMBLEM_SIZE = 200
EMBLEM_COLOR = (104, 96, 145)
TITLE_YELLOW = (242, 214, 41)
TITLE_WHITE = (247, 247, 244)
ALT_TITLE_CROP = (70, 60, 1170, 558)

def composite_replacement_title(pixels, title_pixels, rows) -> tuple[int, int]:
    """Extract the supplied title contours while rejecting its starfield."""
    left, top, right, bottom = ALT_TITLE_CROP
    crop_width = right - left
    crop_height = bottom - top
    scale = min((WIDTH - 8) / crop_width, HEIGHT / crop_height)
    output_width = round(crop_width * scale)
    output_height = round(crop_height * scale)
    output_left = (WIDTH - output_width) // 2
    output_top = (HEIGHT - output_height) // 2

    for y in range(output_height):
        sy0 = top + y * crop_height / output_height
        sy1 = top + (y + 1) * crop_height / output_height
        source_y = (sy0 + sy1) / 2
        for x in range(output_width):
            sx0 = left + x * crop_width / output_width
            sx1 = left + (x + 1) * crop_width / output_width
            r, g, b, alpha = sample_area(rows, sx0, sy0, sx1, sy1)
            color = None
            if (
                alpha > 96 and r > 42 and g > 38
                and r > b * 1.45 and g > b * 1.35
            ):
                color = TITLE_YELLOW
            elif (
                335 <= source_y <= 425
                and 320 <= (sx0 + sx1) / 2 <= 830
                and alpha > 96 and min(r, g, b) > 70
                and max(r, g, b) - min(r, g, b) < 55
            ):
                color = TITLE_WHITE
            if color is not None:
                px = output_left + x
                py = output_top + y
                pixels[py][px] = color
                title_pixels[py][px] = True
    return output_width, output_height


def convert_to_hires(pixels, title_pixels):
    bitmap = bytearray(8000)
    colors = bytearray(1000)
    rendered = [[PALETTE[0]] * WIDTH for _ in range(HEIGHT)]
    for cell_y in range(25):
        for cell_x in range(40):
            visible = []
            mask = []
            for y in range(8):
                for x in range(8):
                    px = cell_x * 8 + x
                    py = cell_y * 8 + y
                    pixel = pixels[py][px]
                    yellow_path = (
                        pixel[0] > 35
                        and pixel[1] > 30
                        and pixel[0] > pixel[2] * 1.6
                        and pixel[1] > pixel[2] * 1.5
                    )
                    threshold = 26 if yellow_path else (
                        52 + (BAYER_4X4[py & 3][px & 3] + 0.5) * 11
                    )
                    active = display_tone(pixel) > threshold
                    mask.append(active)
                    if active:
                        visible.append((pixel, title_pixels[py][px]))

            if any(
                r > 35 and g > 30 and r > b * 1.6 and g > b * 1.5
                for (r, g, b), _ in visible
            ):
                ink = 7
            elif any(is_title and max(pixel) > 120
                     for pixel, is_title in visible):
                ink = 15
            elif visible:
                average = tuple(
                    sum(pixel[channel] for pixel, _ in visible) // len(visible)
                    for channel in range(3)
                )
                ink = min(INKS,
                          key=lambda color: color_error(average, PALETTE[color]))
            else:
                ink = 1
            colors[cell_y * 40 + cell_x] = ink

            for y in range(8):
                value = 0
                py = cell_y * 8 + y
                for x in range(8):
                    px = cell_x * 8 + x
                    active = mask[y * 8 + x]
                    if active:
                        value |= 0x80 >> x
                    rendered[py][px] = PALETTE[ink] if active else PALETTE[0]
                bitmap[cell_y * 320 + cell_x * 8 + y] = value
    return bitmap, colors, rendered


def write_rotation_tables(bitmap, colors) -> int:
    """Select stable emblem cells for an eight-phase rotating highlight."""
    groups = [[] for _ in range(8)]
    center_x = 19.5
    center_y = 12.0
    for cell in range(1000):
        if colors[cell] != 12:
            continue
        cell_x = cell % 40
        cell_y = cell // 40
        radius = math.hypot(cell_x - center_x, cell_y - center_y)
        if not 4.0 <= radius <= 13.0:
            continue
        angle = math.degrees(math.atan2(
            center_y - cell_y, cell_x - center_x)) % 60.0
        phase = min(7, int(angle * 8 / 60.0))
        ink = sum(byte.bit_count() for byte in bitmap[cell * 8:cell * 8 + 8])
        groups[phase].append((ink, radius, cell))

    selected = []
    starts = []
    lengths = []
    for candidates in groups:
        starts.append(len(selected))
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        chosen = []
        for candidate in candidates:
            cell = candidate[2]
            x = cell % 40
            y = cell // 40
            if all(abs(x - other % 40) + abs(y - other // 40) >= 2
                   for other in chosen):
                chosen.append(cell)
            if len(chosen) == 6:
                break
        for candidate in candidates:
            if len(chosen) == 6:
                break
            if candidate[2] not in chosen:
                chosen.append(candidate[2])
        selected.extend(chosen)
        lengths.append(len(chosen))

    def bytes_line(label, values):
        return f"{label}:\n!byte " + ",".join(f"${value:02x}" for value in values)

    lines = [
        "; Generated by scripts/generate_prelude_image.py.",
        bytes_line("prelude_rotation_group_starts", starts),
        bytes_line("prelude_rotation_group_lengths", lengths),
        bytes_line("prelude_rotation_cell_lo", [cell & 0xff for cell in selected]),
        bytes_line("prelude_rotation_cell_hi", [cell >> 8 for cell in selected]),
        "",
    ]
    ROTATION_INCLUDE_OUT.write_text("\n".join(lines), encoding="ascii")
    return len(selected)


def main() -> None:
    source_width, source_height, source_rows = decode_png(SOURCE)
    alt_source_width, alt_source_height, alt_source_rows = decode_png(
        ALT_TITLE_SOURCE)
    left, top, right, bottom = VECTOR_CROP
    crop_width = right - left
    crop_height = bottom - top
    scale = min(WIDTH / crop_width, HEIGHT / crop_height)
    content_width = round(crop_width * scale)
    content_height = round(crop_height * scale)
    offset_x = (WIDTH - content_width) // 2
    offset_y = (HEIGHT - content_height) // 2

    pixels = [[PALETTE[0]] * WIDTH for _ in range(HEIGHT)]
    alt_pixels = [[PALETTE[0]] * WIDTH for _ in range(HEIGHT)]
    title_pixels = [[False] * WIDTH for _ in range(HEIGHT)]
    alt_title_pixels = [[False] * WIDTH for _ in range(HEIGHT)]

    emblem_width, emblem_height, emblem_rows = decode_png(EMBLEM_SOURCE)
    emblem_left = (WIDTH - EMBLEM_SIZE) // 2
    emblem_top = (HEIGHT - EMBLEM_SIZE) // 2
    for y in range(EMBLEM_SIZE):
        sy0 = y * emblem_height / EMBLEM_SIZE
        sy1 = (y + 1) * emblem_height / EMBLEM_SIZE
        for x in range(EMBLEM_SIZE):
            sx0 = x * emblem_width / EMBLEM_SIZE
            sx1 = (x + 1) * emblem_width / EMBLEM_SIZE
            _, _, tone, alpha = sample_area(
                emblem_rows, sx0, sy0, sx1, sy1)
            if alpha > 48 and tone > 24:
                pixels[emblem_top + y][emblem_left + x] = EMBLEM_COLOR

    for y in range(content_height):
        sy0 = top + y * crop_height / content_height
        sy1 = top + (y + 1) * crop_height / content_height
        for x in range(content_width):
            sx0 = left + x * crop_width / content_width
            sx1 = left + (x + 1) * crop_width / content_width
            r, g, b, alpha = sample_area(source_rows, sx0, sy0, sx1, sy1)
            if alpha > 32 and max(r, g, b) > 8:
                pixels[offset_y + y][offset_x + x] = (r, g, b)
                title_pixels[offset_y + y][offset_x + x] = True

    alt_title_width, alt_title_height = composite_replacement_title(
        alt_pixels, alt_title_pixels, alt_source_rows)

    bitmap, colors, rendered = convert_to_hires(pixels, title_pixels)
    alt_bitmap, alt_colors, alt_rendered = convert_to_hires(
        alt_pixels, alt_title_pixels)
    rotation_cells = write_rotation_tables(bitmap, colors)

    PREVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    BITMAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_rgb_png(PREVIEW_OUT, rendered)
    write_rgb_png(ALT_PREVIEW_OUT, alt_rendered)
    BITMAP_OUT.write_bytes(bitmap)
    BITMAP_PRG_OUT.write_bytes(bytes((0x00, 0xe0)) + bitmap)
    COLOR_OUT.write_bytes(colors)
    COLOR_PRG_OUT.write_bytes(bytes((0x00, 0xd8)) + colors)
    ALT_BITMAP_OUT.write_bytes(alt_bitmap)
    ALT_BITMAP_PRG_OUT.write_bytes(bytes((0x00, 0xe0)) + alt_bitmap)
    ALT_COLOR_OUT.write_bytes(alt_colors)
    ALT_COLOR_PRG_OUT.write_bytes(bytes((0x00, 0xd8)) + alt_colors)
    packed_colors = bytearray()
    color_codes = {1: 0, 7: 1, 12: 2, 15: 3}
    for offset in range(0, len(alt_colors), 4):
        packed = 0
        for index, color in enumerate(alt_colors[offset:offset + 4]):
            packed |= color_codes.get(color, 2) << (index * 2)
        packed_colors.append(packed)
    ALT_COLOR_PACKED_OUT.write_bytes(packed_colors)
    ALT_COLOR_PACKED_PRG_OUT.write_bytes(bytes((0x00, 0x02)) + packed_colors)
    print(
        f"Wrote {PREVIEW_OUT.relative_to(ROOT)} ({source_width}x{source_height}, "
        f"crop={crop_width}x{crop_height}@{left},{top}, "
        f"fit={content_width}x{content_height}@{offset_x},{offset_y}, "
        f"emblem={EMBLEM_SIZE}x{EMBLEM_SIZE}@{emblem_left},{emblem_top}), "
        f"replacement={alt_source_width}x{alt_source_height} to "
        f"{alt_title_width}x{alt_title_height}, "
        f"two {len(bitmap)}-byte bitmap frames, two {len(colors)}-byte color "
        f"frames, and {len(packed_colors)} packed alternate-color bytes"
        f"; {rotation_cells} cells drive the rotating emblem highlight"
    )


if __name__ == "__main__":
    main()
