#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


SPRITE_SIZE = 24
FACE_SIZE = 20
FACE_OFFSET = 2
ROW_BYTES = 3
MASK_BYTES = SPRITE_SIZE * ROW_BYTES
BOARD_SIZE = 5
BOARD_LEFT = 69
BOARD_TOP = 8
CELL_PITCH_X = 29
CELL_PITCH_Y = 30
DIE_LEFTS = (70, 98, 128, 158, 186)
DIE_TOPS = (8, 38, 68, 99, 129)
SIDEBAR_DIE_LEFT = 247
SIDEBAR_SOURCE_COLUMN = 2
BLIT_ROWS = SPRITE_SIZE
BLIT_ROW_BYTES = 5
BLIT_BANK_BYTES = BLIT_ROWS * BLIT_ROW_BYTES
BLIT_VARIANT_BYTES = BLIT_BANK_BYTES * 2
MIN_BLIT_BANK_BYTES = 2
DIE_NAMES = ("one", "two", "three", "four", "five", "six")
DIE_COLORS = (
    (245, 245, 245),
    (245, 245, 245),
    (245, 245, 245),
    (245, 245, 245),
    (245, 245, 245),
    (245, 245, 245),
)
FACE_BLIT_BYTES = len(DIE_NAMES) * BOARD_SIZE * BLIT_VARIANT_BYTES
INVALID_BLIT_OFFSET = FACE_BLIT_BYTES
BLITS_BYTES = INVALID_BLIT_OFFSET + BOARD_SIZE * BLIT_VARIANT_BYTES
GRID_PAGE_BYTES = 8192
GRID_A2FM_BYTES = GRID_PAGE_BYTES * 2
EDGE_RESTORE_BYTES = BOARD_SIZE * BOARD_SIZE * BLIT_ROWS
FACE_ROW_INSETS = (4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 4)
PIP_ROW_BITS = (0x06, 0x0F, 0x0F, 0x06)
PIP_POSITIONS = (
    (),
    ((10, 10),),
    ((5, 5), (15, 15)),
    ((5, 5), (10, 10), (15, 15)),
    ((5, 5), (15, 5), (5, 15), (15, 15)),
    ((5, 5), (15, 5), (10, 10), (5, 15), (15, 15)),
    ((5, 5), (15, 5), (5, 10), (15, 10), (5, 15), (15, 15)),
)
DHGR_SIGNAL_WIDTH = SPRITE_SIZE * 2
DHGR_FACE_MARGIN = 4
DHGR_FACE_ROW_INSETS = (8, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 8)
DHGR_PIP_ROWS = (0x0F8, 0x7FE, 0xFFF, 0x7FE, 0x0F8)
DHGR_PIP_POSITIONS = (
    (),
    ((18, 10),),
    ((10, 4), (26, 16)),
    ((10, 4), (18, 10), (26, 16)),
    ((10, 4), (26, 4), (10, 16), (26, 16)),
    ((10, 4), (26, 4), (18, 10), (10, 16), (26, 16)),
    ((10, 4), (26, 4), (10, 10), (26, 10), (10, 16), (26, 16)),
)


def validate_source(path: Path) -> None:
    with Image.open(path) as source:
        source.verify()


def build_face_mask(value: int) -> bytearray:
    if value < 1 or value > 6:
        raise ValueError(f"die value must be 1-6, got {value}")

    mask = bytearray(SPRITE_SIZE * SPRITE_SIZE)
    for local_y, inset in enumerate(FACE_ROW_INSETS):
        y = local_y + FACE_OFFSET
        for x in range(FACE_OFFSET + inset, FACE_OFFSET + FACE_SIZE - inset):
            mask[y * SPRITE_SIZE + x] = 1

    for pip_x, pip_y in PIP_POSITIONS[value]:
        for row, bits in enumerate(PIP_ROW_BITS):
            for col in range(4):
                if bits & (1 << col):
                    mask[(pip_y + row) * SPRITE_SIZE + pip_x + col] = 0
    return mask


def build_dhgr_face_mask(value: int) -> bytearray:
    if value < 1 or value > 6:
        raise ValueError(f"die value must be 1-6, got {value}")

    mask = build_dhgr_body_mask()
    for pip_x, pip_y in DHGR_PIP_POSITIONS[value]:
        for row, bits in enumerate(DHGR_PIP_ROWS):
            for col in range(12):
                if bits & (1 << col):
                    mask[(pip_y + row) * DHGR_SIGNAL_WIDTH + pip_x + col] = 0
    return mask


def build_dhgr_body_mask() -> bytearray:
    mask = bytearray(DHGR_SIGNAL_WIDTH * SPRITE_SIZE)
    for local_y, inset in enumerate(DHGR_FACE_ROW_INSETS):
        y = local_y + FACE_OFFSET
        for x in range(
            DHGR_FACE_MARGIN + inset,
            DHGR_SIGNAL_WIDTH - DHGR_FACE_MARGIN - inset,
        ):
            mask[y * DHGR_SIGNAL_WIDTH + x] = 1
    return mask


def build_dhgr_invalid_mask() -> bytearray:
    body = build_dhgr_body_mask()
    mask = bytearray(len(body))
    for y in range(SPRITE_SIZE):
        for signal in range(DHGR_SIGNAL_WIDTH):
            index = y * DHGR_SIGNAL_WIDTH + signal
            if not body[index]:
                continue
            boundary = (
                signal < 2
                or signal + 2 >= DHGR_SIGNAL_WIDTH
                or y == 0
                or y + 1 == SPRITE_SIZE
                or not body[index - 2]
                or not body[index + 2]
                or not body[index - DHGR_SIGNAL_WIDTH]
                or not body[index + DHGR_SIGNAL_WIDTH]
            )
            if boundary or ((signal // 2 + y) % 6) < 2:
                mask[index] = 1
    return mask


def pack_mask(mask: bytearray) -> bytearray:
    packed = bytearray(MASK_BYTES)
    for y in range(SPRITE_SIZE):
        for x in range(SPRITE_SIZE):
            if mask[y * SPRITE_SIZE + x]:
                packed[y * ROW_BYTES + x // 8] |= 1 << (x & 7)
    return packed


def hgr_address(y: int) -> int:
    return 0x2000 + ((y & 0x07) << 10) + (((y >> 3) & 0x07) << 7) + (y >> 6) * 0x28


def bank_span(column: int, auxiliary: bool) -> tuple[int, int]:
    return bank_span_at(DIE_LEFTS[column], auxiliary)


def bank_span_at(origin_x: int, auxiliary: bool) -> tuple[int, int]:
    first = (origin_x * 2) // 7
    last = (origin_x * 2 + SPRITE_SIZE * 2 - 1) // 7
    parity = 0 if auxiliary else 1
    sequence_bytes = [byte for byte in range(first, last + 1) if byte & 1 == parity]
    offsets = [byte // 2 for byte in sequence_bytes]
    if len(offsets) < MIN_BLIT_BANK_BYTES:
        bank = "auxiliary" if auxiliary else "main"
        raise AssertionError(
            f"DHGR {bank} span at x={origin_x} contains {len(offsets)} byte(s); "
            f"assembly blitters require at least {MIN_BLIT_BANK_BYTES}"
        )
    return min(offsets), len(offsets)


def bank_masks(column: int, auxiliary: bool) -> tuple[int, int]:
    return bank_masks_at(DIE_LEFTS[column], auxiliary)


def bank_masks_at(origin_x: int, auxiliary: bool) -> tuple[int, int]:
    left = origin_x * 2
    right = left + SPRITE_SIZE * 2 - 1
    offset, count = bank_span_at(origin_x, auxiliary)
    parity = 0 if auxiliary else 1
    sequence_bytes = [
        byte
        for byte in range(left // 7, right // 7 + 1)
        if byte & 1 == parity
    ]
    first_mask = sum(
        1 << (signal % 7)
        for signal in range(left, right + 1)
        if signal // 7 == sequence_bytes[0]
    )
    last_mask = sum(
        1 << (signal % 7)
        for signal in range(left, right + 1)
        if signal // 7 == sequence_bytes[-1]
    )
    if offset != sequence_bytes[0] // 2 or count != len(sequence_bytes):
        raise AssertionError("inconsistent DHGR bank span")
    return first_mask, last_mask


def build_edge_restores(grid: bytes, auxiliary: bool, first: bool) -> list[int]:
    if len(grid) != GRID_A2FM_BYTES:
        raise ValueError("grid A2FM must contain 8 KB auxiliary and main pages")
    bank = grid[:GRID_PAGE_BYTES] if auxiliary else grid[GRID_PAGE_BYTES:]
    restores = []
    for column in range(BOARD_SIZE):
        byte_offset, byte_count = bank_span(column, auxiliary)
        first_mask, last_mask = bank_masks(column, auxiliary)
        edge_offset = byte_offset if first else byte_offset + byte_count - 1
        sprite_mask = first_mask if first else last_mask
        for board_row in range(BOARD_SIZE):
            for line in range(BLIT_ROWS):
                address = hgr_address(DIE_TOPS[board_row] + line) - 0x2000
                restores.append(bank[address + edge_offset] & (0xFF ^ sprite_mask))
    if len(restores) != EDGE_RESTORE_BYTES:
        raise AssertionError("unexpected grid edge restore table size")
    return restores


def compact_edge_restores(grid: bytes) -> tuple[list[int], list[list[int]]]:
    tables = [
        build_edge_restores(grid, True, True),
        build_edge_restores(grid, True, False),
        build_edge_restores(grid, False, True),
        build_edge_restores(grid, False, False),
    ]
    pool: list[int] = []
    chunk_offsets: dict[tuple[int, ...], int] = {}
    table_offsets: list[list[int]] = []
    for table in tables:
        offsets = []
        for start in range(0, len(table), BLIT_ROWS):
            chunk = tuple(table[start : start + BLIT_ROWS])
            offset = chunk_offsets.get(chunk)
            if offset is None:
                offset = len(pool)
                chunk_offsets[chunk] = offset
                pool.extend(chunk)
            offsets.append(offset)
        table_offsets.append(offsets)
    return pool, table_offsets


def set_signal(
    blit: bytearray,
    signal_x: int,
    row: int,
    pattern: int,
    bank_offset: int,
    auxiliary: bool,
) -> None:
    if not pattern & (1 << (3 - (signal_x & 3))):
        return
    sequence_byte = signal_x // 7
    if (sequence_byte & 1) != (0 if auxiliary else 1):
        return
    target = row * BLIT_ROW_BYTES + sequence_byte // 2 - bank_offset
    blit[target] |= 1 << (signal_x % 7)


def set_pixel(
    blit: bytearray,
    x: int,
    row: int,
    pattern: int,
    bank_offset: int,
    auxiliary: bool,
) -> None:
    set_signal(blit, x * 2, row, pattern, bank_offset, auxiliary)
    set_signal(blit, x * 2 + 1, row, pattern, bank_offset, auxiliary)


def set_color_pixel(
    blit: bytearray,
    x: int,
    row: int,
    pattern: int,
    bank_offset: int,
    auxiliary: bool,
) -> None:
    signal_x = x * 4
    for bit in range(4):
        set_signal(blit, signal_x + bit, row, pattern, bank_offset, auxiliary)


def render_face_bank(mask: bytearray, value: int, column: int, auxiliary: bool) -> bytearray:
    blit = bytearray(BLIT_BANK_BYTES)
    bank_offset, _ = bank_span(column, auxiliary)
    for row in range(SPRITE_SIZE):
        for signal in range(DHGR_SIGNAL_WIDTH):
            if mask[row * DHGR_SIGNAL_WIDTH + signal]:
                set_signal(
                    blit,
                    DIE_LEFTS[column] * 2 + signal,
                    row,
                    0x0F,
                    bank_offset,
                    auxiliary,
                )
    return blit


def join_banks(auxiliary: bytearray, main: bytearray) -> bytearray:
    if len(auxiliary) != BLIT_BANK_BYTES or len(main) != BLIT_BANK_BYTES:
        raise AssertionError("unexpected DHGR sprite bank size")
    return auxiliary + main


def build_blits(masks: list[bytearray]) -> bytearray:
    blits = bytearray()
    invalid_mask = build_dhgr_invalid_mask()
    for value, mask in enumerate(masks, 1):
        for column in range(BOARD_SIZE):
            blits.extend(join_banks(
                render_face_bank(mask, value, column, True),
                render_face_bank(mask, value, column, False),
            ))
    for column in range(BOARD_SIZE):
        blits.extend(join_banks(
            render_face_bank(invalid_mask, 0, column, True),
            render_face_bank(invalid_mask, 0, column, False),
        ))
    if len(blits) != BLITS_BYTES:
        raise AssertionError(f"unexpected dice blit size: {len(blits)}")
    return blits


def format_array(name: str, data: bytearray | list[int], declaration: str = "static const unsigned char") -> str:
    lines = [f"{declaration} {name}[{len(data)}] = {{"]
    for offset in range(0, len(data), 12):
        values = ", ".join(f"0x{value:02X}" for value in data[offset : offset + 12])
        lines.append(f"    {values},")
    lines.append("};")
    return "\n".join(lines)


def format_u16_array(name: str, data: list[int]) -> str:
    lines = [f"static const unsigned {name}[{len(data)}] = {{"]
    for offset in range(0, len(data), 8):
        values = ", ".join(f"{value}u" for value in data[offset : offset + 8])
        lines.append(f"    {values},")
    lines.append("};")
    return "\n".join(lines)


def write_header(
    path: Path,
    masks: list[bytearray],
    dhgr_masks: list[bytearray],
    grid: bytes,
) -> None:
    blits = build_blits(dhgr_masks)
    edge_pool, edge_offsets = compact_edge_restores(grid)
    aux_byte_counts = [bank_span(column, True)[1] for column in range(BOARD_SIZE)]
    main_byte_counts = [bank_span(column, False)[1] for column in range(BOARD_SIZE)]
    sidebar_aux_byte_count = bank_span_at(SIDEBAR_DIE_LEFT, True)[1]
    sidebar_main_byte_count = bank_span_at(SIDEBAR_DIE_LEFT, False)[1]
    minimum_byte_count = min(
        aux_byte_counts
        + main_byte_counts
        + [sidebar_aux_byte_count, sidebar_main_byte_count]
    )
    row_addresses = [
        hgr_address(DIE_TOPS[board_row] + line)
        for board_row in range(BOARD_SIZE)
        for line in range(BLIT_ROWS)
    ]
    sections = [
        "#ifndef SIXIES_DICE_ASSETS_H",
        "#define SIXIES_DICE_ASSETS_H",
        "",
        f"#define DICE_ASSET_SIZE {SPRITE_SIZE}",
        f"#define DICE_ASSET_ROW_BYTES {ROW_BYTES}",
        f"#define DICE_BLIT_ROWS {BLIT_ROWS}",
        f"#define DICE_BLIT_ROW_BYTES {BLIT_ROW_BYTES}",
        f"#define DICE_BLIT_BANK_BYTES {BLIT_BANK_BYTES}",
        f"#define DICE_MIN_BLIT_BYTE_COUNT {minimum_byte_count}",
        f"#define DICE_BLIT_VARIANT_BYTES {BLIT_VARIANT_BYTES}",
        f"#define DICE_FACE_BLITS_BYTES {FACE_BLIT_BYTES}",
        f"#define DICE_INVALID_BLIT_OFFSET {INVALID_BLIT_OFFSET}",
        f"#define DICE_BLITS_BYTES {BLITS_BYTES}",
        f"#define DICE_BLITS_CHECKSUM {sum(blits) & 0xFFFF}u",
        f"#define DICE_EDGE_RESTORE_BYTES {EDGE_RESTORE_BYTES}",
        f"#define DICE_SIDEBAR_SOURCE_COLUMN {SIDEBAR_SOURCE_COLUMN}",
        f"#define DICE_SIDEBAR_AUX_BYTE_OFFSET {bank_span_at(SIDEBAR_DIE_LEFT, True)[0]}",
        f"#define DICE_SIDEBAR_MAIN_BYTE_OFFSET {bank_span_at(SIDEBAR_DIE_LEFT, False)[0]}",
        f"#define DICE_SIDEBAR_AUX_BYTE_COUNT {sidebar_aux_byte_count}",
        f"#define DICE_SIDEBAR_MAIN_BYTE_COUNT {sidebar_main_byte_count}",
        "",
    ]
    for name, mask in zip(DIE_NAMES, masks):
        sections.extend((format_array(f"die_{name}_face_mask", pack_mask(mask)), ""))
    sections.extend((
        format_u16_array(
            "dice_face_blit_offsets",
            [index * BLIT_VARIANT_BYTES for index in range(len(DIE_NAMES) * BOARD_SIZE)],
        ),
        "",
        format_u16_array(
            "dice_invalid_blit_offsets",
            [INVALID_BLIT_OFFSET + column * BLIT_VARIANT_BYTES for column in range(BOARD_SIZE)],
        ),
        "",
        format_array(
            "dice_aux_byte_offsets",
            [bank_span(column, True)[0] for column in range(BOARD_SIZE)],
        ),
        "",
        format_array(
            "dice_aux_byte_counts",
            aux_byte_counts,
        ),
        "",
        format_array(
            "dice_aux_first_masks",
            [bank_masks(column, True)[0] for column in range(BOARD_SIZE)],
        ),
        "",
        format_array(
            "dice_aux_last_masks",
            [bank_masks(column, True)[1] for column in range(BOARD_SIZE)],
        ),
        "",
        format_array(
            "dice_main_byte_offsets",
            [bank_span(column, False)[0] for column in range(BOARD_SIZE)],
        ),
        "",
        format_array(
            "dice_main_byte_counts",
            main_byte_counts,
        ),
        "",
        format_array(
            "dice_main_first_masks",
            [bank_masks(column, False)[0] for column in range(BOARD_SIZE)],
        ),
        "",
        format_array(
            "dice_main_last_masks",
            [bank_masks(column, False)[1] for column in range(BOARD_SIZE)],
        ),
        "",
        format_array(
            "dice_edge_restore_pool",
            edge_pool,
        ),
        "",
        format_u16_array(
            "dice_aux_first_restore_offsets",
            edge_offsets[0],
        ),
        "",
        format_u16_array(
            "dice_aux_last_restore_offsets",
            edge_offsets[1],
        ),
        "",
        format_u16_array(
            "dice_main_first_restore_offsets",
            edge_offsets[2],
        ),
        "",
        format_u16_array(
            "dice_main_last_restore_offsets",
            edge_offsets[3],
        ),
        "",
        format_array(
            "dice_blit_row_low",
            [address & 0xFF for address in row_addresses],
            "const unsigned char",
        ),
        "",
        format_array(
            "dice_blit_row_high",
            [address >> 8 for address in row_addresses],
            "const unsigned char",
        ),
        "",
    ))
    sections.extend(("#endif", ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sections), encoding="ascii")


def write_preview(path: Path, masks: list[bytearray]) -> None:
    gap = 8
    width = SPRITE_SIZE * len(masks) + gap * (len(masks) - 1)
    image = Image.new("RGB", (width, SPRITE_SIZE), (5, 11, 14))
    pixels = image.load()
    for index, (mask, color) in enumerate(zip(masks, DIE_COLORS)):
        offset = index * (SPRITE_SIZE + gap)
        for y in range(SPRITE_SIZE):
            for x in range(SPRITE_SIZE):
                signal = x * 2
                if mask[y * DHGR_SIGNAL_WIDTH + signal] or mask[
                    y * DHGR_SIGNAL_WIDTH + signal + 1
                ]:
                    pixels[x + offset, y] = color
    path.parent.mkdir(parents=True, exist_ok=True)
    image.resize((width * 8, SPRITE_SIZE * 8), Image.Resampling.NEAREST).save(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate HGR dice masks from source artwork")
    parser.add_argument("--one", required=True, type=Path)
    parser.add_argument("--two", required=True, type=Path)
    parser.add_argument("--three", required=True, type=Path)
    parser.add_argument("--four", required=True, type=Path)
    parser.add_argument("--five", required=True, type=Path)
    parser.add_argument("--six", required=True, type=Path)
    parser.add_argument("--grid", required=True, type=Path)
    parser.add_argument("--header", required=True, type=Path)
    parser.add_argument("--blits", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sources = [getattr(args, name) for name in DIE_NAMES]
    for source in sources:
        validate_source(source)
    masks = [build_face_mask(value) for value in range(1, 7)]
    dhgr_masks = [build_dhgr_face_mask(value) for value in range(1, 7)]
    blits = build_blits(dhgr_masks)
    grid = args.grid.read_bytes()
    write_header(args.header, masks, dhgr_masks, grid)
    args.blits.parent.mkdir(parents=True, exist_ok=True)
    args.blits.write_bytes(blits)
    write_preview(args.preview, dhgr_masks)


if __name__ == "__main__":
    main()
