#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_presents.py"
MASTER = APPLE2_DIR / "assets" / "presents_master.ppm"
SPEC = importlib.util.spec_from_file_location("generate_presents", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class PresentsGenerationTests(unittest.TestCase):
    def test_rle_round_trips_literals_runs_and_boundaries(self) -> None:
        source = bytes(range(128)) + bytes((7,)) * 128 + bytes(range(127, -1, -1))
        packed = GENERATOR.pack_rle(source)
        self.assertEqual(GENERATOR.unpack_rle(packed, len(source)), source)

    def test_presents_master_fits_startup_dice_buffer(self) -> None:
        indexed = GENERATOR.CONVERTER.render_source(
            MASTER,
            GENERATOR.CONVERTER.PAGE_HEIGHT,
            "none",
        )
        main, auxiliary = GENERATOR.CONVERTER.to_pages(indexed)
        packed_auxiliary = GENERATOR.pack_rle(auxiliary)
        packed_main = GENERATOR.pack_rle(main)

        self.assertEqual(len(packed_auxiliary), 4188)
        self.assertEqual(len(packed_main), 4207)
        self.assertLessEqual(
            len(packed_auxiliary) + len(packed_main),
            GENERATOR.MAX_PACKED_BYTES,
        )


if __name__ == "__main__":
    unittest.main()
