#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_hgr_dice.py"
MASTERS = [APPLE2_DIR / "assets" / f"die_{value}_master.png" for value in range(1, 7)]
GRID = APPLE2_DIR / "assets" / "game_grid_dhgr_mono_master.a2fm"
SPEC = importlib.util.spec_from_file_location("generate_hgr_dice", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class HgrDiceTests(unittest.TestCase):
    def test_masks_have_clean_symmetric_faces_and_exact_pips(self) -> None:
        masks = [GENERATOR.build_face_mask(value) for value in range(1, 7)]
        base_pixels = sum(GENERATOR.build_face_mask(1)) + 12

        for value, mask in enumerate(masks, 1):
            self.assertEqual(sum(mask), base_pixels - value * 12)
            self.assertEqual(mask[0], 0)
            for y in range(GENERATOR.SPRITE_SIZE):
                for x in range(GENERATOR.SPRITE_SIZE):
                    opposite = (
                        (GENERATOR.SPRITE_SIZE - 1 - y) * GENERATOR.SPRITE_SIZE
                        + GENERATOR.SPRITE_SIZE - 1 - x
                    )
                    self.assertEqual(mask[y * GENERATOR.SPRITE_SIZE + x], mask[opposite])
        center_pips = [
            any(
                mask[y * GENERATOR.SPRITE_SIZE + x] == 0
                for y in range(11, 13)
                for x in range(11, 13)
            )
            for mask in masks
        ]
        self.assertEqual(center_pips, [True, False, True, False, True, False])

    def test_packed_masks_have_three_bytes_per_row(self) -> None:
        for value in range(1, 7):
            packed = GENERATOR.pack_mask(GENERATOR.build_face_mask(value))
            self.assertEqual(len(packed), GENERATOR.MASK_BYTES)

    def test_dhgr_faces_use_native_monochrome_signals(self) -> None:
        self.assertTrue(all(origin % 2 == 0 for origin in GENERATOR.DIE_LEFTS))
        pip_pixels = sum(bits.bit_count() for bits in GENERATOR.DHGR_PIP_ROWS)
        base_pixels = sum(GENERATOR.build_dhgr_face_mask(1)) + pip_pixels
        for value in range(1, 7):
            mask = GENERATOR.build_dhgr_face_mask(value)
            self.assertEqual(
                len(mask),
                GENERATOR.DHGR_SIGNAL_WIDTH * GENERATOR.SPRITE_SIZE,
            )
            self.assertTrue(any(mask))
            self.assertEqual(sum(mask), base_pixels - value * pip_pixels)

    def test_precomputed_blits_cover_every_face_and_column(self) -> None:
        masks = [GENERATOR.build_dhgr_face_mask(value) for value in range(1, 7)]
        blits = GENERATOR.build_blits(masks)

        self.assertEqual(len(blits), GENERATOR.BLITS_BYTES)
        for value in range(6):
            for column in range(GENERATOR.BOARD_SIZE):
                offset = (value * GENERATOR.BOARD_SIZE + column) * GENERATOR.BLIT_VARIANT_BYTES
                variant = blits[offset : offset + GENERATOR.BLIT_VARIANT_BYTES]
                self.assertTrue(any(variant[:GENERATOR.BLIT_BANK_BYTES]))
                self.assertTrue(any(variant[GENERATOR.BLIT_BANK_BYTES:]))

    def test_banked_blits_reconstruct_expected_dhgr_signals(self) -> None:
        masks = [GENERATOR.build_dhgr_face_mask(value) for value in range(1, 7)]
        blits = GENERATOR.build_blits(masks)

        for value, mask in enumerate(masks, 1):
            for column in range(GENERATOR.BOARD_SIZE):
                variant_offset = (
                    ((value - 1) * GENERATOR.BOARD_SIZE + column)
                    * GENERATOR.BLIT_VARIANT_BYTES
                )
                for y in range(GENERATOR.SPRITE_SIZE):
                    for local_signal in range(GENERATOR.DHGR_SIGNAL_WIDTH):
                        signal = GENERATOR.DIE_LEFTS[column] * 2 + local_signal
                        sequence_byte = signal // 7
                        auxiliary = sequence_byte & 1 == 0
                        bank_offset, _ = GENERATOR.bank_span(column, auxiliary)
                        source_offset = variant_offset
                        if not auxiliary:
                            source_offset += GENERATOR.BLIT_BANK_BYTES
                        source_offset += y * GENERATOR.BLIT_ROW_BYTES
                        source_offset += sequence_byte // 2 - bank_offset
                        actual = bool(blits[source_offset] & (1 << (signal % 7)))
                        expected = bool(mask[y * GENERATOR.DHGR_SIGNAL_WIDTH + local_signal])
                        self.assertEqual(actual, expected)

    def test_invalid_variants_are_precomputed(self) -> None:
        masks = [GENERATOR.build_dhgr_face_mask(value) for value in range(1, 7)]
        blits = GENERATOR.build_blits(masks)
        invalid = GENERATOR.build_dhgr_invalid_mask()
        body = GENERATOR.build_dhgr_body_mask()

        self.assertGreater(sum(invalid), 200)
        self.assertLess(sum(invalid), sum(body))
        self.assertTrue(all(not pixel or body[index] for index, pixel in enumerate(invalid)))

        for column in range(GENERATOR.BOARD_SIZE):
            offset = GENERATOR.INVALID_BLIT_OFFSET + column * GENERATOR.BLIT_VARIANT_BYTES
            variant = blits[offset : offset + GENERATOR.BLIT_VARIANT_BYTES]
            self.assertTrue(any(variant[:GENERATOR.BLIT_BANK_BYTES]))
            self.assertTrue(any(variant[GENERATOR.BLIT_BANK_BYTES:]))

    def test_board_scanline_table_covers_five_24_row_tiles(self) -> None:
        addresses = [
            GENERATOR.hgr_address(
                GENERATOR.DIE_TOPS[board_row] + line
            )
            for board_row in range(GENERATOR.BOARD_SIZE)
            for line in range(GENERATOR.BLIT_ROWS)
        ]
        self.assertEqual(len(addresses), GENERATOR.BOARD_SIZE * GENERATOR.BLIT_ROWS)
        self.assertTrue(all(0x2000 <= address < 0x4000 for address in addresses))

    def test_sidebar_is_centered_with_an_existing_sprite_phase(self) -> None:
        self.assertEqual(GENERATOR.SIDEBAR_DIE_LEFT, 238)
        self.assertEqual(GENERATOR.SIDEBAR_SOURCE_COLUMN, 0)
        column = GENERATOR.SIDEBAR_SOURCE_COLUMN
        for auxiliary in (True, False):
            _, source_count = GENERATOR.bank_span(column, auxiliary)
            target_offset, target_count = GENERATOR.bank_span_at(
                GENERATOR.SIDEBAR_DIE_LEFT,
                auxiliary,
            )
            self.assertEqual(target_offset, 34)
            self.assertEqual(target_count, source_count)
            self.assertEqual(
                GENERATOR.bank_masks_at(GENERATOR.SIDEBAR_DIE_LEFT, auxiliary),
                GENERATOR.bank_masks(column, auxiliary),
            )

    def test_every_assembly_blit_span_has_first_and_last_bytes(self) -> None:
        byte_counts = [
            GENERATOR.bank_span(column, auxiliary)[1]
            for column in range(GENERATOR.BOARD_SIZE)
            for auxiliary in (True, False)
        ]
        byte_counts.extend(
            GENERATOR.bank_span_at(GENERATOR.SIDEBAR_DIE_LEFT, auxiliary)[1]
            for auxiliary in (True, False)
        )

        self.assertGreaterEqual(min(byte_counts), GENERATOR.MIN_BLIT_BANK_BYTES)

    def test_generator_rejects_a_one_byte_bank_span(self) -> None:
        with patch.object(GENERATOR, "SPRITE_SIZE", 1):
            with self.assertRaisesRegex(AssertionError, "require at least 2"):
                GENERATOR.bank_span_at(0, True)

    def test_blit_rows_touch_only_the_selected_board_cell_span(self) -> None:
        masks = [GENERATOR.build_dhgr_face_mask(value) for value in range(1, 7)]
        blits = GENERATOR.build_blits(masks)

        for board_row in range(GENERATOR.BOARD_SIZE):
            for column in range(GENERATOR.BOARD_SIZE):
                source_offset = column * GENERATOR.BLIT_VARIANT_BYTES
                source = blits[source_offset : source_offset + GENERATOR.BLIT_VARIANT_BYTES]
                y = GENERATOR.DIE_TOPS[board_row]
                for auxiliary, bank_start in ((True, 0), (False, GENERATOR.BLIT_BANK_BYTES)):
                    page = bytearray(8192)
                    byte_offset, byte_count = GENERATOR.bank_span(column, auxiliary)
                    expected_addresses = set()
                    for line in range(GENERATOR.BLIT_ROWS):
                        target = GENERATOR.hgr_address(y + line) - 0x2000 + byte_offset
                        source_row = bank_start + line * GENERATOR.BLIT_ROW_BYTES
                        for byte in range(byte_count):
                            page[target + byte] |= source[source_row + byte]
                            expected_addresses.add(target + byte)
                    changed = {index for index, value in enumerate(page) if value}
                    self.assertTrue(changed)
                    self.assertLessEqual(changed, expected_addresses)

    def test_blit_checksum_is_stable(self) -> None:
        masks = [GENERATOR.build_dhgr_face_mask(value) for value in range(1, 7)]
        blits = GENERATOR.build_blits(masks)
        self.assertEqual(sum(blits) & 0xFFFF, 36591)

    def test_edge_restore_tables_match_original_grid_banks(self) -> None:
        grid = GRID.read_bytes()
        for auxiliary in (True, False):
            bank_start = 0 if auxiliary else GENERATOR.GRID_PAGE_BYTES
            bank = grid[bank_start : bank_start + GENERATOR.GRID_PAGE_BYTES]
            for first in (True, False):
                restores = GENERATOR.build_edge_restores(grid, auxiliary, first)
                self.assertEqual(len(restores), GENERATOR.EDGE_RESTORE_BYTES)
                for column in range(GENERATOR.BOARD_SIZE):
                    byte_offset, byte_count = GENERATOR.bank_span(column, auxiliary)
                    first_mask, last_mask = GENERATOR.bank_masks(column, auxiliary)
                    edge_offset = byte_offset if first else byte_offset + byte_count - 1
                    sprite_mask = first_mask if first else last_mask
                    for row in range(GENERATOR.BOARD_SIZE):
                        for line in range(GENERATOR.BLIT_ROWS):
                            table_index = (
                                column * GENERATOR.BOARD_SIZE * GENERATOR.BLIT_ROWS
                                + row * GENERATOR.BLIT_ROWS
                                + line
                            )
                            address = GENERATOR.hgr_address(
                                GENERATOR.DIE_TOPS[row] + line
                            ) - 0x2000
                            self.assertEqual(
                                restores[table_index],
                                bank[address + edge_offset] & (0xFF ^ sprite_mask),
                            )

    def test_edge_restore_chunks_are_compact_and_exact(self) -> None:
        grid = GRID.read_bytes()
        pool, offsets = GENERATOR.compact_edge_restores(grid)
        self.assertEqual(len(pool), 360)
        self.assertEqual([len(values) for values in offsets], [25, 25, 25, 25])
        expected_tables = [
            GENERATOR.build_edge_restores(grid, True, True),
            GENERATOR.build_edge_restores(grid, True, False),
            GENERATOR.build_edge_restores(grid, False, True),
            GENERATOR.build_edge_restores(grid, False, False),
        ]
        for expected, table_offsets in zip(expected_tables, offsets):
            rebuilt = []
            for offset in table_offsets:
                rebuilt.extend(pool[offset : offset + GENERATOR.BLIT_ROWS])
            self.assertEqual(rebuilt, expected)

    def test_every_cell_write_clear_restores_grid_byte_exactly(self) -> None:
        grid = GRID.read_bytes()
        masks = [GENERATOR.build_dhgr_face_mask(value) for value in range(1, 7)]
        blits = GENERATOR.build_blits(masks)
        for auxiliary in (True, False):
            bank_start = 0 if auxiliary else GENERATOR.GRID_PAGE_BYTES
            original = grid[bank_start : bank_start + GENERATOR.GRID_PAGE_BYTES]
            first_restores = GENERATOR.build_edge_restores(grid, auxiliary, True)
            last_restores = GENERATOR.build_edge_restores(grid, auxiliary, False)
            for column in range(GENERATOR.BOARD_SIZE):
                byte_offset, byte_count = GENERATOR.bank_span(column, auxiliary)
                first_mask, last_mask = GENERATOR.bank_masks(column, auxiliary)
                variant = column * GENERATOR.BLIT_VARIANT_BYTES
                if not auxiliary:
                    variant += GENERATOR.BLIT_BANK_BYTES
                for row in range(GENERATOR.BOARD_SIZE):
                    page = bytearray(original)
                    edge = (
                        column * GENERATOR.BOARD_SIZE * GENERATOR.BLIT_ROWS
                        + row * GENERATOR.BLIT_ROWS
                    )
                    for line in range(GENERATOR.BLIT_ROWS):
                        destination = (
                            GENERATOR.hgr_address(GENERATOR.DIE_TOPS[row] + line)
                            - 0x2000
                            + byte_offset
                        )
                        source = variant + line * GENERATOR.BLIT_ROW_BYTES
                        page[destination] = (
                            first_restores[edge + line] | (blits[source] & first_mask)
                        )
                        for byte in range(1, byte_count - 1):
                            page[destination + byte] = blits[source + byte]
                        page[destination + byte_count - 1] = (
                            last_restores[edge + line]
                            | (blits[source + byte_count - 1] & last_mask)
                        )
                    for line in range(GENERATOR.BLIT_ROWS):
                        destination = (
                            GENERATOR.hgr_address(GENERATOR.DIE_TOPS[row] + line)
                            - 0x2000
                            + byte_offset
                        )
                        page[destination] = first_restores[edge + line]
                        for byte in range(1, byte_count - 1):
                            page[destination + byte] = 0
                        page[destination + byte_count - 1] = last_restores[edge + line]
                    self.assertEqual(page, original)


if __name__ == "__main__":
    unittest.main()
