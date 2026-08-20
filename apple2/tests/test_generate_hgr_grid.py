#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_hgr_grid.py"
MASTER = Path(__file__).parents[1] / "assets" / "grid_master.png"
SPEC = importlib.util.spec_from_file_location("generate_hgr_grid", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


def packed_pixel(page: bytearray, x: int, y: int) -> bool:
    address = GENERATOR.row_offset(y) + x // 7
    return bool(page[address] & (1 << (x % 7)))


class HgrGridTests(unittest.TestCase):
    def setUp(self) -> None:
        self.canvas = GENERATOR.build_canvas(MASTER)
        self.page = GENERATOR.pack_hgr(self.canvas)

    def test_page_shape_and_imported_grid(self) -> None:
        self.assertEqual(len(self.page), GENERATOR.PAGE_BYTES)
        board_pixels = sum(
            packed_pixel(self.page, x, y)
            for y in range(6, 147)
            for x in range(6, 147)
        )
        self.assertGreater(board_pixels, 500)
        self.assertFalse(packed_pixel(self.page, 20, 20))

    def test_dirty_tiles_match_hgr_page(self) -> None:
        tiles = GENERATOR.pack_grid_tiles(self.page)
        self.assertEqual(len(tiles), GENERATOR.TILES_BYTES)
        first_line = self.page[
            GENERATOR.row_offset(GENERATOR.BOARD_BITMAP_TOP) :
            GENERATOR.row_offset(GENERATOR.BOARD_BITMAP_TOP) + 5
        ]
        self.assertEqual(tiles[:5], first_line)

    def test_dynamic_sidebar_well_is_empty(self) -> None:
        for y in range(24, 86):
            for x in range(174, 258):
                self.assertFalse(packed_pixel(self.page, x, y))

    def test_static_labels_and_footer_are_present(self) -> None:
        self.assertTrue(packed_pixel(self.page, 179, 15))
        self.assertTrue(packed_pixel(self.page, 179, 103))
        self.assertTrue(packed_pixel(self.page, 236, 153))


if __name__ == "__main__":
    unittest.main()
