#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_game_over.py"
MASTER = APPLE2_DIR / "assets" / "game_over_master.png"
SPEC = importlib.util.spec_from_file_location("generate_game_over", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GAME_OVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GAME_OVER)


class GenerateGameOverTests(unittest.TestCase):
    def test_art_is_title_compatible_monochrome_dhgr(self) -> None:
        image = GAME_OVER.render_game_over(MASTER)
        main, auxiliary = GAME_OVER.GENERATOR.to_mono_pages(image)
        decoded = GAME_OVER.A2FM.decode_mono(main, auxiliary)

        self.assertEqual(image.size, (560, 192))
        self.assertEqual(set(image.tobytes()), {0, 255})
        self.assertEqual(decoded.tobytes(), image.tobytes())

    def test_bottom_text_rows_remain_clear(self) -> None:
        image = GAME_OVER.render_game_over(MASTER)

        self.assertIsNone(image.crop((0, GAME_OVER.ART_HEIGHT, 560, 192)).getbbox())

    def test_packed_banks_fit_the_reusable_load_buffer(self) -> None:
        image = GAME_OVER.render_game_over(MASTER)
        main, auxiliary = GAME_OVER.GENERATOR.to_mono_pages(image)

        self.assertLessEqual(
            len(GAME_OVER.GENERATOR.pack_rle(main)),
            GAME_OVER.GENERATOR.MAX_PACKED_BANK_BYTES,
        )
        self.assertLessEqual(
            len(GAME_OVER.GENERATOR.pack_rle(auxiliary)),
            GAME_OVER.GENERATOR.MAX_PACKED_BANK_BYTES,
        )


if __name__ == "__main__":
    unittest.main()
