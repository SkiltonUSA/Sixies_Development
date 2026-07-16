#!/usr/bin/env python3
"""Trace the STAR / RETRODNA / WAR raster into editable SVG geometry."""

from collections import defaultdict, deque
from pathlib import Path
import struct
import zlib

from generate_logo import decode_png
from generate_vader2 import png_chunk


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "assets" / "star_retro_war_vector_source.png"
OUTPUT = ROOT / "src" / "assets" / "star_retro_war_vector.svg"
RENDER_OUTPUT = ROOT / "src" / "assets" / "star_retro_war_vector_render.png"


def pixel(rows, x: int, y: int):
    return rows[y][x * 4:x * 4 + 4]


def write_rgb_image(path: Path, rows) -> None:
    height = len(rows)
    width = len(rows[0])
    raw = b"".join(
        b"\x00" + b"".join(bytes(pixel_value) for pixel_value in row)
        for row in rows
    )
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )


def connected_components(mask: set[tuple[int, int]], diagonal: bool = False):
    remaining = set(mask)
    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if diagonal:
        neighbors += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    while remaining:
        seed = remaining.pop()
        component = {seed}
        queue = deque((seed,))
        while queue:
            x, y = queue.popleft()
            for dx, dy in neighbors:
                point = (x + dx, y + dy)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    queue.append(point)
        yield component


def retained_mask(mask: set[tuple[int, int]], minimum: int) -> set[tuple[int, int]]:
    retained = set()
    for component in connected_components(mask):
        if len(component) >= minimum:
            retained.update(component)
    return retained


def close_mask(mask: set[tuple[int, int]], radius: int) -> set[tuple[int, int]]:
    offsets = tuple(
        (dx, dy)
        for dy in range(-radius, radius + 1)
        for dx in range(-radius, radius + 1)
    )
    dilated = {
        (x + dx, y + dy)
        for x, y in mask
        for dx, dy in offsets
    }
    return {
        (x, y)
        for x, y in dilated
        if all((x + dx, y + dy) in dilated for dx, dy in offsets)
    }


def edge_direction(edge):
    x0, y0, x1, y1 = edge
    return {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}[
        (x1 - x0, y1 - y0)
    ]


def trace_loops(mask: set[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    edges = set()
    for x, y in mask:
        if (x, y - 1) not in mask:
            edges.add((x, y, x + 1, y))
        if (x + 1, y) not in mask:
            edges.add((x + 1, y, x + 1, y + 1))
        if (x, y + 1) not in mask:
            edges.add((x + 1, y + 1, x, y + 1))
        if (x - 1, y) not in mask:
            edges.add((x, y + 1, x, y))

    outgoing = defaultdict(set)
    for edge in edges:
        outgoing[(edge[0], edge[1])].add(edge)

    loops = []
    while edges:
        edge = next(iter(edges))
        edges.remove(edge)
        start = (edge[0], edge[1])
        point = (edge[2], edge[3])
        direction = edge_direction(edge)
        loop = [start, point]

        while point != start:
            candidates = [candidate for candidate in outgoing[point] if candidate in edges]
            if not candidates:
                break
            preference = (
                (direction + 1) & 3,
                direction,
                (direction - 1) & 3,
                (direction + 2) & 3,
            )
            candidate = min(
                candidates,
                key=lambda item: preference.index(edge_direction(item)),
            )
            edges.remove(candidate)
            direction = edge_direction(candidate)
            point = (candidate[2], candidate[3])
            loop.append(point)

        if len(loop) >= 4 and loop[-1] == start:
            loops.append(simplify_loop(loop[:-1]))
    return loops


def point_line_distance(point, start, end) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    return abs(dy * px - dx * py + bx * ay - by * ax) / (dx * dx + dy * dy) ** 0.5


def simplify_open(points: list[tuple[int, int]], tolerance: float):
    if len(points) <= 2:
        return points
    start = points[0]
    end = points[-1]
    distances = [
        point_line_distance(point, start, end)
        for point in points[1:-1]
    ]
    if not distances:
        return (start, end)
    distance = max(distances)
    if distance <= tolerance:
        return (start, end)
    index = distances.index(distance) + 1
    left = simplify_open(points[:index + 1], tolerance)
    right = simplify_open(points[index:], tolerance)
    return (*left[:-1], *right)


def simplify_loop(points: list[tuple[int, int]], tolerance: float = 1.15):
    if len(points) <= 3:
        return points
    anchor = points[0]
    split = max(
        range(1, len(points)),
        key=lambda index: (
            (points[index][0] - anchor[0]) ** 2
            + (points[index][1] - anchor[1]) ** 2
        ),
    )
    first = simplify_open(points[:split + 1], tolerance)
    second = simplify_open(points[split:] + [anchor], tolerance)
    simplified = [*first[:-1], *second[:-1]]
    return simplified if len(simplified) >= 3 else points


def path_data(mask: set[tuple[int, int]]) -> str:
    commands = []
    for loop in trace_loops(mask):
        commands.append(f"M{loop[0][0]} {loop[0][1]}")
        commands.extend(f"L{x} {y}" for x, y in loop[1:])
        commands.append("Z")
    return "".join(commands)


def component_paths(mask: set[tuple[int, int]], prefix: str):
    components = sorted(
        connected_components(mask),
        key=lambda component: min((y, x) for x, y in component),
    )
    return [
        f'<path id="{prefix}-{index + 1}" d="{path_data(component)}" '
        'fill-rule="evenodd"/>'
        for index, component in enumerate(components)
    ]


def star_elements(rows, width, height, excluded):
    bright = set()
    for y in range(height):
        for x in range(width):
            if (x, y) in excluded:
                continue
            r, g, b, a = pixel(rows, x, y)
            if a > 96 and max(r, g, b) > 105 and (r + g + b) > 235:
                bright.add((x, y))

    elements = []
    shapes = []
    for component in connected_components(bright, diagonal=True):
        if not 1 <= len(component) <= 130:
            continue
        xs = [point[0] for point in component]
        ys = [point[1] for point in component]
        box_width = max(xs) - min(xs) + 1
        box_height = max(ys) - min(ys) + 1
        if box_width > 15 or box_height > 15:
            continue
        samples = [pixel(rows, x, y) for x, y in component]
        red = sum(sample[0] for sample in samples) // len(samples)
        green = sum(sample[1] for sample in samples) // len(samples)
        blue = sum(sample[2] for sample in samples) // len(samples)
        opacity = min(0.92, 0.30 + len(component) / 20)
        cx = (min(xs) + max(xs) + 1) / 2
        cy = (min(ys) + max(ys) + 1) / 2
        rx = max(0.45, box_width / 2)
        ry = max(0.45, box_height / 2)
        elements.append(
            f'<ellipse cx="{cx:g}" cy="{cy:g}" rx="{rx:g}" ry="{ry:g}" '
            f'fill="rgb({red},{green},{blue})" opacity="{opacity:.2f}"/>'
        )
        shapes.append((cx, cy, rx, ry, red, green, blue, opacity))
    return elements, shapes


def render_scene(width, height, star_shapes, yellow, white_word):
    background = (2, 3, 7)
    rendered = [[background] * width for _ in range(height)]
    for cx, cy, rx, ry, red, green, blue, opacity in star_shapes:
        left = max(0, int(cx - rx))
        right = min(width, int(cx + rx + 1))
        top = max(0, int(cy - ry))
        bottom = min(height, int(cy + ry + 1))
        for y in range(top, bottom):
            for x in range(left, right):
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                if dx * dx + dy * dy > 1:
                    continue
                old = rendered[y][x]
                rendered[y][x] = tuple(
                    round(old[channel] * (1 - opacity) + color * opacity)
                    for channel, color in enumerate((red, green, blue))
                )
    for x, y in yellow:
        rendered[y][x] = (242, 214, 41)
    for x, y in white_word:
        rendered[y][x] = (247, 247, 244)
    return rendered


def main() -> None:
    width, height, rows = decode_png(SOURCE)
    yellow = set()
    white_word = set()
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixel(rows, x, y)
            if a < 64:
                continue
            in_title_band = 55 <= x <= 785 and (
                55 <= y <= 250 or 335 <= y <= 550
            )
            if (
                in_title_band
                and r > 115
                and g > 95
                and b < 115
                and r + g > b * 3
            ):
                yellow.add((x, y))
            if 185 <= x <= 685 and 245 <= y <= 330:
                if min(r, g, b) > 145 and max(r, g, b) - min(r, g, b) < 50:
                    white_word.add((x, y))

    yellow = retained_mask(close_mask(yellow, radius=2), minimum=100)
    white_word = retained_mask(white_word, minimum=100)
    stars, star_shapes = star_elements(rows, width, height, yellow | white_word)
    yellow_paths = component_paths(yellow, "yellow-outline")
    white_paths = component_paths(white_word, "retrodna-glyph")

    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">',
        "  <title>STAR RETRODNA WAR vector trace</title>",
        '  <rect id="background" width="100%" height="100%" fill="#020307"/>',
        '  <g id="starfield">',
        *(f"    {star}" for star in stars),
        "  </g>",
        '  <g id="yellow-outlines" fill="#f2d629">',
        *(f"    {path}" for path in yellow_paths),
        "  </g>",
        '  <g id="retrodna-lettering" fill="#f7f7f4">',
        *(f"    {path}" for path in white_paths),
        "  </g>",
        "</svg>",
        "",
    ]
    OUTPUT.write_text("\n".join(svg), encoding="ascii")
    write_rgb_image(
        RENDER_OUTPUT,
        render_scene(width, height, star_shapes, yellow, white_word),
    )
    print(
        f"Wrote {OUTPUT.relative_to(ROOT)} and "
        f"{RENDER_OUTPUT.relative_to(ROOT)} with {len(stars)} vector stars, "
        f"{len(yellow_paths)} yellow components, and "
        f"{len(white_paths)} white glyph components"
    )


if __name__ == "__main__":
    main()
