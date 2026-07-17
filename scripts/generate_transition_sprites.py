#!/usr/bin/env python3
"""Convert the supplied ship artwork into layered 48x42 C64 images."""

from pathlib import Path
import math

from generate_logo import decode_png

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "src" / "assets" / "transition_ships_reference.png"
PLASMA_TIE_SOURCE_PATH = ROOT / "src" / "assets" / "plasma_tie_reference.png"
TIE_EMBLEM_SOURCE_PATH = ROOT / "src" / "assets" / "transition_tie_emblem.png"
XWING_EMBLEM_SOURCE_PATH = ROOT / "src" / "assets" / "transition_xwing_emblem.png"
OUTPUT_PATH = ROOT / "src" / "generated" / "transition_sprites.inc"
PLASMA_OUTPUT_PATH = ROOT / "src" / "generated" / "plasma_tie_sprite.inc"
EMBLEM_OUTPUT_PATH = ROOT / "src" / "generated" / "transition_emblems.inc"

TIE_SOURCE_CROP = (235, 200, 470, 480)
TIE_OUTPUT_SIZE = (35, 42)
XWING_SOURCE_CROP = (785, 560, 1390, 780)
XWING_OUTPUT_SIZE = (48, 21)
COMPOSITE_WIDTH = 48
COMPOSITE_HEIGHT = 42
SPRITE_WIDTH = 24
SPRITE_HEIGHT = 21
PLASMA_TIE_SIZE = (10, 17)
PLASMA_TIE_FRAMES = 4
PLASMA_TIE_PATH_STEPS = 64
PLASMA_TIE_SOURCE_THRESHOLD = 32
PLASMA_TIE_DETAIL_TONE = 120
PLASMA_TIE_CELL_COVERAGE = 0.025
PLASMA_BOB_WIDTH = 12
PLASMA_BOB_HEIGHT = 21
TRANSITION_EMBLEMS = (
    ("tie", TIE_EMBLEM_SOURCE_PATH, 24, 48, 40),
    ("xwing", XWING_EMBLEM_SOURCE_PATH, 272, 128, 40),
)


def tie_pixel_class(r: int, g: int, b: int) -> int:
    """Return 0=space, 1=dark source detail, or 2=light hull."""
    if max(r, g, b) < 22:
        return 0
    if b > r * 1.12 and b > g * 1.12:
        return 1
    return 2


def xwing_pixel_class(r: int, g: int, b: int) -> int:
    """Return 0=space, 1=orange marking, or 2=gray hull."""
    if max(r, g, b) < 22:
        return 0
    if r > g * 1.12 and r > b * 1.12:
        return 1
    return 2


def reduce_ship(rows, source_crop, output_size, classifier):
    left, top, right, bottom = source_crop
    out_width, out_height = output_size
    crop_width = right - left
    crop_height = bottom - top
    pixels = [[0] * out_width for _ in range(out_height)]

    for out_y in range(out_height):
        iy0 = int(top + out_y * crop_height / out_height)
        iy1 = max(iy0 + 1, int(top + (out_y + 1) * crop_height
                              / out_height + 0.999))
        for out_x in range(out_width):
            ix0 = int(left + out_x * crop_width / out_width)
            ix1 = max(ix0 + 1, int(left + (out_x + 1) * crop_width
                                  / out_width + 0.999))
            counts = [0, 0, 0]
            for src_y in range(iy0, iy1):
                row = rows[src_y]
                for src_x in range(ix0, ix1):
                    offset = src_x * 4
                    r, g, b = row[offset:offset + 3]
                    counts[classifier(r, g, b)] += 1

            samples = sum(counts)
            if (counts[1] + counts[2]) * 9 < samples:
                continue
            pixels[out_y][out_x] = 1 if counts[1] > counts[2] else 2

    # Carve solid hull interiors back to black so the source outlines and
    # mechanical gaps remain readable at the reduced resolution.
    outlined = [row[:] for row in pixels]
    for y in range(1, out_height - 1):
        for x in range(1, out_width - 1):
            if pixels[y][x] != 2:
                continue
            if all(pixels[ny][nx] != 0
                   for nx, ny in ((x - 1, y), (x + 1, y),
                                  (x, y - 1), (x, y + 1))):
                outlined[y][x] = 0
    return outlined


def place_composite(ship):
    canvas = [[0] * COMPOSITE_WIDTH for _ in range(COMPOSITE_HEIGHT)]
    offset_x = (COMPOSITE_WIDTH - len(ship[0])) // 2
    offset_y = (COMPOSITE_HEIGHT - len(ship)) // 2
    for y, row in enumerate(ship):
        for x, value in enumerate(row):
            canvas[offset_y + y][offset_x + x] = value
    return canvas


def quadrant_to_sprite(canvas, quadrant_x, quadrant_y, layer):
    data = bytearray()
    origin_x = quadrant_x * SPRITE_WIDTH
    origin_y = quadrant_y * SPRITE_HEIGHT
    for y in range(SPRITE_HEIGHT):
        bits = 0
        for x in range(SPRITE_WIDTH):
            active = canvas[origin_y + y][origin_x + x] == layer
            bits = (bits << 1) | active
        data.extend(((bits >> 16) & 0xff, (bits >> 8) & 0xff, bits & 0xff))
    data.append(0)
    return data


def emit_bytes(lines, data):
    for start in range(0, len(data), 16):
        values = ",".join(f"${value:02x}" for value in data[start:start + 16])
        lines.append(f"    !byte {values}")


def reduce_emblem(rows, width: int, height: int, output_size: int):
    left = width
    top = height
    right = 0
    bottom = 0
    for y, row in enumerate(rows):
        for x in range(width):
            offset = x * 4
            r, g, b, a = row[offset:offset + 4]
            if a > 32 and max(r, g, b) > 96:
                left = min(left, x)
                top = min(top, y)
                right = max(right, x + 1)
                bottom = max(bottom, y + 1)
    if right <= left or bottom <= top:
        raise ValueError("transition emblem source contains no white pixels")

    crop_width = right - left
    crop_height = bottom - top
    pixels = [[0] * output_size for _ in range(output_size)]
    for out_y in range(output_size):
        y0 = int(top + out_y * crop_height / output_size)
        y1 = max(y0 + 1, math.ceil(top + (out_y + 1) *
                                    crop_height / output_size))
        for out_x in range(output_size):
            x0 = int(left + out_x * crop_width / output_size)
            x1 = max(x0 + 1, math.ceil(left + (out_x + 1) *
                                        crop_width / output_size))
            white = 0
            samples = 0
            for source_y in range(y0, y1):
                row = rows[source_y]
                for source_x in range(x0, x1):
                    offset = source_x * 4
                    r, g, b, a = row[offset:offset + 4]
                    samples += 1
                    if a > 32 and (r * 2 + g * 3 + b) / 6 > 128:
                        white += 1
            if white * 2 >= samples:
                pixels[out_y][out_x] = 1
    return pixels, (left, top, right, bottom)


def emblem_bitmap_masks(pixels, dest_x: int, dest_y: int):
    height = len(pixels)
    width = len(pixels[0])
    if dest_x & 7:
        raise ValueError("transition emblem x position must be byte aligned")
    if width % 8:
        raise ValueError("transition emblem width must be a whole byte count")
    bytes_per_row = width // 8
    rows = []
    for y in range(height):
        screen_y = dest_y + y
        if not 0 <= screen_y < 200:
            continue
        row_masks = []
        for byte_index in range(bytes_per_row):
            mask = 0xff
            for bit_index in range(8):
                x = byte_index * 8 + bit_index
                if pixels[y][x]:
                    mask &= ~(1 << (7 - bit_index))
            row_masks.append(mask)
        rows.append(row_masks)
    return rows


def emblem_screen_cells(pixels, dest_x: int, dest_y: int):
    height = len(pixels)
    width = len(pixels[0])
    cells = set()
    for y in range(height):
        screen_y = dest_y + y
        if not 0 <= screen_y < 200:
            continue
        for x in range(width):
            if not pixels[y][x]:
                continue
            screen_x = dest_x + x
            if 0 <= screen_x < 320:
                cells.add((screen_y // 8) * 40 + (screen_x // 8))
    return sorted(cells)


def write_transition_emblems() -> None:
    lines = [
        "; Generated by scripts/generate_transition_sprites.py.",
        "; Bitmap masks stamp white faction emblems into the flyby starfield.",
    ]
    summaries = []
    for name, path, dest_x, dest_y, size in TRANSITION_EMBLEMS:
        width, height, rows = decode_png(path)
        pixels, crop = reduce_emblem(rows, width, height, size)
        masks = emblem_bitmap_masks(pixels, dest_x, dest_y)
        cells = emblem_screen_cells(pixels, dest_x, dest_y)
        flat_masks = [mask for row in masks for mask in row]
        if len(flat_masks) > 255 or len(cells) > 255:
            raise ValueError(f"{name} emblem exceeds one-byte table count")
        row_addresses = []
        byte_x = dest_x // 8
        for row_index in range(len(masks)):
            screen_y = dest_y + row_index
            char_row = screen_y // 8
            row_in_cell = screen_y & 7
            row_addresses.append(0xe000 + char_row * 320 +
                                 byte_x * 8 + row_in_cell)
        lines.append(f"TRANSITION_{name.upper()}_EMBLEM_ROW_COUNT = {len(masks)}")
        lines.append(f"TRANSITION_{name.upper()}_EMBLEM_BYTES_PER_ROW = {len(masks[0])}")
        lines.append(f"transition_{name}_emblem_row_addr_lo:")
        emit_bytes(lines, [address & 0xff for address in row_addresses])
        lines.append(f"transition_{name}_emblem_row_addr_hi:")
        emit_bytes(lines, [(address >> 8) & 0xff for address in row_addresses])
        lines.append(f"transition_{name}_emblem_mask:")
        emit_bytes(lines, flat_masks)
        summaries.append(
            f"{name}={size}px@{dest_x},{dest_y} crop={crop} "
            f"{len(flat_masks)} mask bytes/{len(cells)} cells")
    EMBLEM_OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"Wrote {EMBLEM_OUTPUT_PATH.relative_to(ROOT)} "
          f"({', '.join(summaries)})")


def rotate_to_sprite(ship, angle: float) -> bytes:
    """Rotate a compact TIE into one 24x21 single-color hires sprite."""
    source_height = len(ship)
    source_width = len(ship[0])
    source_cx = (source_width - 1) / 2
    source_cy = (source_height - 1) / 2
    output_cx = (SPRITE_WIDTH - 1) / 2
    output_cy = (SPRITE_HEIGHT - 1) / 2
    cosine = math.cos(angle)
    sine = math.sin(angle)
    data = bytearray()

    for y in range(SPRITE_HEIGHT):
        bits = 0
        for x in range(SPRITE_WIDTH):
            dx = x - output_cx
            dy = y - output_cy
            source_x = round(source_cx + dx * cosine + dy * sine)
            source_y = round(source_cy - dx * sine + dy * cosine)
            active = (0 <= source_x < source_width and
                      0 <= source_y < source_height and
                      ship[source_y][source_x] != 0)
            bits = (bits << 1) | active
        data.extend(((bits >> 16) & 0xff, (bits >> 8) & 0xff, bits & 0xff))
    data.append(0)
    return bytes(data)


def build_round_multicolor_sprite(emblem, angle: float):
    bob = [[0] * PLASMA_BOB_WIDTH for _ in range(PLASMA_BOB_HEIGHT)]
    emblem_offset_x = (PLASMA_BOB_WIDTH - len(emblem[0])) // 2
    emblem_offset_y = (PLASMA_BOB_HEIGHT - len(emblem)) // 2
    center_x = (PLASMA_BOB_WIDTH - 1) / 2
    center_y = (PLASMA_BOB_HEIGHT - 1) / 2
    cosine = math.cos(angle)
    sine = math.sin(angle)
    for y in range(PLASMA_BOB_HEIGHT):
        for x in range(PLASMA_BOB_WIDTH):
            dx = (x - center_x) / 5.75
            dy = (y - center_y) / 10.25
            if dx * dx + dy * dy <= 1:
                screen_x = (x - center_x) * 2
                screen_y = y - center_y
                source_x = round(center_x +
                                 (screen_x * cosine + screen_y * sine) / 2)
                source_y = round(center_y - screen_x * sine +
                                 screen_y * cosine)
                emblem_x = source_x - emblem_offset_x
                emblem_y = source_y - emblem_offset_y
                if (0 <= emblem_x < len(emblem[0]) and
                        0 <= emblem_y < len(emblem) and
                        emblem[emblem_y][emblem_x]):
                    bob[y][x] = 2       # light-gray TIE fighter
                else:
                    bob[y][x] = 1       # opaque dark-blue field
    return bob


def pack_multicolor_sprite(bob) -> bytes:
    """Pack a 12x21 matrix of two-bit values into C64 sprite data."""
    data = bytearray()
    for y in range(PLASMA_BOB_HEIGHT):
        row_values = []
        for x in range(PLASMA_BOB_WIDTH):
            row_values.append(bob[y][x])
        for start in range(0, PLASMA_BOB_WIDTH, 4):
            packed = 0
            for value in row_values[start:start + 4]:
                packed = (packed << 2) | value
            data.append(packed)
    data.append(0)
    return bytes(data)


def extract_plasma_tie(rows, width: int, height: int):
    """Isolate the ship, discard stars, and retain bright source detail."""
    foreground = bytearray(width * height)
    for y, row in enumerate(rows):
        for x in range(width):
            offset = x * 4
            r, g, b, a = row[offset:offset + 4]
            if a > 32 and max(r, g, b) >= PLASMA_TIE_SOURCE_THRESHOLD:
                foreground[y * width + x] = 1

    seen = bytearray(width * height)
    components = []
    for start, active in enumerate(foreground):
        if not active or seen[start]:
            continue
        component = [start]
        seen[start] = 1
        cursor = 0
        while cursor < len(component):
            index = component[cursor]
            cursor += 1
            y, x = divmod(index, width)
            for nx, ny in ((x - 1, y), (x + 1, y),
                           (x, y - 1), (x, y + 1)):
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                neighbor = ny * width + nx
                if foreground[neighbor] and not seen[neighbor]:
                    seen[neighbor] = 1
                    component.append(neighbor)
        components.append(component)

    if not components:
        raise ValueError("plasma bob source contains no foreground component")

    largest_size = max(len(component) for component in components)
    retained = [component for component in components
                if len(component) >= largest_size * 0.05]
    retained_pixels = [index for component in retained for index in component]
    component_mask = bytearray(width * height)
    for index in retained_pixels:
        component_mask[index] = 1
    min_x = min(index % width for index in retained_pixels)
    max_x = max(index % width for index in retained_pixels) + 1
    min_y = min(index // width for index in retained_pixels)
    max_y = max(index // width for index in retained_pixels) + 1

    output_width, output_height = PLASMA_TIE_SIZE
    tie = [[0] * output_width for _ in range(output_height)]
    for out_y in range(output_height):
        y0 = int(min_y + out_y * (max_y - min_y) / output_height)
        y1 = max(y0 + 1, math.ceil(
            min_y + (out_y + 1) * (max_y - min_y) / output_height))
        for out_x in range(output_width):
            x0 = int(min_x + out_x * (max_x - min_x) / output_width)
            x1 = max(x0 + 1, math.ceil(
                min_x + (out_x + 1) * (max_x - min_x) / output_width))
            detail = 0
            samples = (x1 - x0) * (y1 - y0)
            for source_y in range(y0, y1):
                row = rows[source_y]
                for source_x in range(x0, x1):
                    if not component_mask[source_y * width + source_x]:
                        continue
                    offset = source_x * 4
                    r, g, b = row[offset:offset + 3]
                    tone = (r * 2 + g * 3 + b) / 6
                    if tone >= PLASMA_TIE_DETAIL_TONE:
                        detail += 1
            if detail / samples >= PLASMA_TIE_CELL_COVERAGE:
                tie[out_y][out_x] = 1
    return (tie, (min_x, min_y, max_x, max_y), len(retained_pixels),
            len(retained))


def write_plasma_tie() -> None:
    width, height, rows = decode_png(PLASMA_TIE_SOURCE_PATH)
    tie, crop, component_size, component_count = extract_plasma_tie(
        rows, width, height)
    sprites = [build_round_multicolor_sprite(
                   tie, frame * math.pi / PLASMA_TIE_FRAMES)
               for frame in range(PLASMA_TIE_FRAMES)]
    frames = [pack_multicolor_sprite(sprite) for sprite in sprites]
    positions = []
    for step in range(PLASMA_TIE_PATH_STEPS):
        angle = step * 2 * math.pi / PLASMA_TIE_PATH_STEPS
        positions.append((
            170 + round(130 * math.cos(angle)),
            min(185, 137 + round(70 * math.sin(angle))),
        ))

    lines = [
        "; Generated by scripts/generate_transition_sprites.py.",
        f"PLASMA_TIE_FRAME_COUNT = {PLASMA_TIE_FRAMES}",
        f"PLASMA_TIE_PATH_STEPS = {PLASMA_TIE_PATH_STEPS}",
        "plasma_tie_sprite_data:",
    ]
    for frame, data in enumerate(frames):
        lines.append(f"; combined circle and TIE fighter, frame {frame}")
        emit_bytes(lines, data)
    lines.append("plasma_tie_path_x_lo:")
    emit_bytes(lines, [x & 0xff for x, _ in positions])
    lines.append("plasma_tie_path_x_hi:")
    emit_bytes(lines, [(x >> 8) & 1 for x, _ in positions])
    lines.append("plasma_tie_path_y:")
    emit_bytes(lines, [y for _, y in positions])
    PLASMA_OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")
    counts = ", ".join(str(sum(value != 0 for row in sprite for value in row))
                       for sprite in sprites)
    print(f"Wrote {PLASMA_OUTPUT_PATH.relative_to(ROOT)} "
          f"from {width}x{height} source, crop={crop}, "
          f"components={component_count}/{component_size}px "
          f"({PLASMA_TIE_FRAMES} combined sprite frames, pixels={counts})")


def main() -> None:
    width, height, rows = decode_png(SOURCE_PATH)
    ships = (
        ("tie", place_composite(reduce_ship(
            rows, TIE_SOURCE_CROP, TIE_OUTPUT_SIZE, tie_pixel_class))),
        ("xwing", place_composite(reduce_ship(
            rows, XWING_SOURCE_CROP, XWING_OUTPUT_SIZE, xwing_pixel_class))),
    )
    lines = [
        "; Generated by scripts/generate_transition_sprites.py.",
        "; TIE then X-wing, four quadrants each, detail layer then hull layer.",
        "shiptransition_sprite_data:",
    ]
    counts = []
    for ship_name, canvas in ships:
        for quadrant_y in range(2):
            for quadrant_x in range(2):
                quadrant_name = ("top" if quadrant_y == 0 else "bottom") + \
                                "-" + ("left" if quadrant_x == 0 else "right")
                for layer, layer_name in ((1, "detail"), (2, "hull")):
                    data = quadrant_to_sprite(
                        canvas, quadrant_x, quadrant_y, layer)
                    lines.append(
                        f"; {ship_name} {quadrant_name} {layer_name}")
                    emit_bytes(lines, data)
                    counts.append((ship_name, quadrant_name, layer_name,
                                   sum(byte.bit_count() for byte in data)))

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="ascii")
    write_plasma_tie()
    write_transition_emblems()
    summary = ", ".join(f"{ship}-{name}-{layer}={count}px"
                        for ship, name, layer, count in counts)
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} from {width}x{height} source "
          f"({summary})")


if __name__ == "__main__":
    main()
