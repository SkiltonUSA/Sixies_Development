#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

from PIL import Image


SCRIPT = Path(__file__).parents[1] / "scripts" / "convert_dhgr_asset.py"
SPEC = importlib.util.spec_from_file_location("convert_dhgr_asset", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CONVERTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONVERTER)


class DhgrPackingTests(unittest.TestCase):
    EXPECTED_FIRST_BYTES = (
        (0x00, 0x00, 0x00, 0x00),
        (0x08, 0x11, 0x22, 0x44),
        (0x11, 0x22, 0x44, 0x08),
        (0x19, 0x33, 0x66, 0x4C),
        (0x22, 0x44, 0x08, 0x11),
        (0x2A, 0x55, 0x2A, 0x55),
        (0x33, 0x66, 0x4C, 0x19),
        (0x3B, 0x77, 0x6E, 0x5D),
        (0x44, 0x08, 0x11, 0x22),
        (0x4C, 0x19, 0x33, 0x66),
        (0x55, 0x2A, 0x55, 0x2A),
        (0x5D, 0x3B, 0x77, 0x6E),
        (0x66, 0x4C, 0x19, 0x33),
        (0x6E, 0x5D, 0x3B, 0x77),
        (0x77, 0x6E, 0x5D, 0x3B),
        (0x7F, 0x7F, 0x7F, 0x7F),
    )

    def test_solid_color_byte_patterns(self) -> None:
        for color, expected in enumerate(self.EXPECTED_FIRST_BYTES):
            image = Image.new("P", (CONVERTER.PAGE_WIDTH, 1), color)
            main, aux = CONVERTER.to_pages(image)
            actual = (aux[0], main[0], aux[1], main[1])
            self.assertEqual(actual, expected, f"DHGR color {color:X}")

    def test_page_round_trip(self) -> None:
        image = Image.new("P", (CONVERTER.PAGE_WIDTH, 1))
        for x in range(CONVERTER.PAGE_WIDTH):
            image.putpixel((x, 0), x & 0x0F)
        main, aux = CONVERTER.to_pages(image)
        decoded = CONVERTER.decode_pages(main, aux, 1)
        self.assertEqual(decoded.tobytes(), image.tobytes())
        self.assertEqual(len(main), CONVERTER.PAGE_BYTES)
        self.assertEqual(len(aux), CONVERTER.PAGE_BYTES)

    def test_source_palette_matching_preserves_chroma(self) -> None:
        self.assertEqual(CONVERTER.nearest_palette_color((129, 57, 148)), 3)
        self.assertEqual(CONVERTER.nearest_palette_color((210, 75, 95)), 11)
        self.assertEqual(CONVERTER.nearest_palette_color((110, 110, 110)), 5)
        self.assertEqual(CONVERTER.nearest_palette_color((235, 235, 115)), 13)

if __name__ == "__main__":
    unittest.main()
