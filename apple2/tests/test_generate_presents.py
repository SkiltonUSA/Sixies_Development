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
        monochrome = GENERATOR.render_mono_source(MASTER)
        main, auxiliary = GENERATOR.to_mono_pages(monochrome)
        packed_auxiliary = GENERATOR.pack_rle(auxiliary)
        packed_main = GENERATOR.pack_rle(main)

        self.assertLessEqual(
            len(packed_auxiliary) + len(packed_main),
            GENERATOR.MAX_PACKED_BYTES,
        )

    def test_presents_uses_title_compatible_monochrome_layout(self) -> None:
        monochrome = GENERATOR.render_mono_source(MASTER)
        main, auxiliary = GENERATOR.to_mono_pages(monochrome)
        decoded = GENERATOR.A2FM.decode_mono(main, auxiliary)
        split_main, split_auxiliary = GENERATOR.A2FM.split_a2fm(auxiliary + main)

        self.assertEqual(
            monochrome.size,
            (GENERATOR.A2FM.SCREEN_WIDTH, GENERATOR.A2FM.SCREEN_HEIGHT),
        )
        self.assertEqual(set(monochrome.tobytes()), {0, 255})
        self.assertEqual(decoded.tobytes(), monochrome.tobytes())
        self.assertEqual((split_main, split_auxiliary), (main, auxiliary))


if __name__ == "__main__":
    unittest.main()
