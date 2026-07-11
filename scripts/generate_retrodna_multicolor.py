#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / ".context" / "attachments" / "q2y3Hi" / "retro dna.png"
OUT = ROOT / "src" / "generated" / "retrodna_multicolor.inc"

CANVAS_W = 320
CANVAS_H = 200
LOGO_W = 304
LOGO_Y_OFFSET = 8
LOGO_ROW_START_THRESHOLD = 48
BITMAP_ADDR = 0x2000
SCREEN_ADDR = 0x0C00
COLOR_SOURCE_ADDR = 0x4000

C64_PALETTE = [
    (0x02, 0x02, 0x02),  # 0 black
    (0xFF, 0xFF, 0xFF),  # 1 white
    (0x68, 0x37, 0x2B),  # 2 red
    (0x70, 0xA4, 0xB2),  # 3 cyan
    (0x6F, 0x3D, 0x86),  # 4 purple
    (0x58, 0x8D, 0x43),  # 5 green
    (0x35, 0x28, 0x79),  # 6 blue
    (0xB8, 0xC7, 0x6F),  # 7 yellow
    (0x6F, 0x4F, 0x25),  # 8 orange
    (0x43, 0x39, 0x00),  # 9 brown
    (0x9A, 0x67, 0x59),  # 10 light red / pink
    (0x44, 0x44, 0x44),  # 11 dark gray
    (0x6C, 0x6C, 0x6C),  # 12 medium gray
    (0x9A, 0xD2, 0x84),  # 13 light green
    (0x6C, 0x5E, 0xB5),  # 14 light blue
    (0x95, 0x95, 0x95),  # 15 light gray
]


def run_ffmpeg() -> bytes:
    vf = f"scale={LOGO_W}:-1:flags=bilinear,pad={CANVAS_W}:{CANVAS_H}:(ow-iw)/2:(oh-ih)/2+{LOGO_Y_OFFSET}:black,format=rgba"
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(INPUT),
        "-vf",
        vf,
        "-frames:v",
        "1",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    return subprocess.check_output(cmd)


def composite_rgba(raw: bytes) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    for i in range(0, len(raw), 4):
        r, g, b, a = raw[i], raw[i + 1], raw[i + 2], raw[i + 3]
        if a == 255:
            pixels.append((r, g, b))
            continue
        alpha = a / 255.0
        pixels.append(
            (
                round(r * alpha),
                round(g * alpha),
                round(b * alpha),
            )
        )
    return pixels


def dist2(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum((x - y) * (x - y) for x, y in zip(a, b))


def nearest_c64(rgb: tuple[int, int, int]) -> int:
    best = 0
    best_d = None
    for idx, pal in enumerate(C64_PALETTE):
        d = dist2(rgb, pal)
        if best_d is None or d < best_d:
            best = idx
            best_d = d
    return best


def clear_sparse_pre_logo_rows(
    pixels: list[tuple[int, int, int]],
) -> list[tuple[int, int, int]]:
    cleaned = pixels[:]
    for y in range(CANVAS_H):
        start = y * CANVAS_W
        row = cleaned[start : start + CANVAS_W]
        coloured = sum(1 for rgb in row if max(rgb) > 24)
        if coloured >= LOGO_ROW_START_THRESHOLD:
            break
        cleaned[start : start + CANVAS_W] = [(0, 0, 0)] * CANVAS_W
    return cleaned


def choose_cell_colors(cell_idx: list[int]) -> tuple[int, int, int]:
    counts = Counter(idx for idx in cell_idx if idx != 0)
    ordered = sorted(counts, key=lambda idx: (-counts[idx], idx))
    ordered.extend([0, 0, 0])
    return ordered[0], ordered[1], ordered[2]


def average_rgb(
    left: tuple[int, int, int], right: tuple[int, int, int]
) -> tuple[int, int, int]:
    return tuple((a + b) // 2 for a, b in zip(left, right))


def build_bitmap(
    pixels: list[tuple[int, int, int]],
) -> tuple[list[int], list[int], list[int]]:
    screen: list[int] = []
    color_ram: list[int] = []
    bitmap = [0] * 8000

    for cy in range(25):
        for cx in range(40):
            cell_indices: list[int] = []
            for py in range(8):
                base = (cy * 8 + py) * CANVAS_W + cx * 8
                for px in range(0, 8, 2):
                    rgb = average_rgb(pixels[base + px], pixels[base + px + 1])
                    cell_indices.append(nearest_c64(rgb))

            color_1, color_2, color_3 = choose_cell_colors(cell_indices)
            palette_indices = [0, color_1, color_2, color_3]
            screen.append((color_1 << 4) | color_2)
            color_ram.append(color_3)

            for py in range(8):
                byte_val = 0
                for px in range(0, 8, 2):
                    base = (cy * 8 + py) * CANVAS_W + cx * 8 + px
                    rgb = average_rgb(pixels[base], pixels[base + 1])
                    code = min(
                        range(4),
                        key=lambda candidate: (
                            dist2(rgb, C64_PALETTE[palette_indices[candidate]]),
                            candidate,
                        ),
                    )
                    byte_val = (byte_val << 2) | code

                bitmap_offset = cy * 320 + cx * 8 + py
                bitmap[bitmap_offset] = byte_val

    return screen, color_ram, bitmap


def emit_bytes(label: str, values: list[int]) -> list[str]:
    lines = [f"{label}:"]
    for i in range(0, len(values), 16):
        chunk = values[i : i + 16]
        lines.append("!byte " + ", ".join(f"${v:02x}" for v in chunk))
    return lines


def write_include(screen: list[int], color_ram: list[int], bitmap: list[int]) -> None:
    lines = [
        "; Generated static RetroDNA multicolour bitmap.",
        f"; Source: {INPUT.relative_to(ROOT)}",
        f"* = ${SCREEN_ADDR:04x}",
        *emit_bytes("retrodna_screen", screen),
        f"* = ${COLOR_SOURCE_ADDR:04x}",
        *emit_bytes("retrodna_color_source", color_ram),
        f"* = ${BITMAP_ADDR:04x}",
        *emit_bytes("retrodna_bitmap", bitmap),
        "",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    raw = run_ffmpeg()
    expected = CANVAS_W * CANVAS_H * 4
    if len(raw) != expected:
        raise RuntimeError(f"unexpected raw frame size: {len(raw)} != {expected}")
    pixels = clear_sparse_pre_logo_rows(composite_rgba(raw))
    screen, color_ram, bitmap = build_bitmap(pixels)
    write_include(screen, color_ram, bitmap)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
