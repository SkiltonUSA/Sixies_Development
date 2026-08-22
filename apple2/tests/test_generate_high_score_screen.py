#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_high_score_screen.py"
DICE = APPLE2_DIR / "assets" / "high_score_dice_master.ppm"
SPEC = importlib.util.spec_from_file_location("generate_high_score_screen", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HIGH_SCORES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HIGH_SCORES)


class GenerateHighScoreScreenTests(unittest.TestCase):
    def test_background_is_round_trip_monochrome_dhgr(self) -> None:
        background = HIGH_SCORES.render_background(DICE)
        main, auxiliary = HIGH_SCORES.GENERATOR.to_mono_pages(background)
        decoded = HIGH_SCORES.GENERATOR.A2FM.decode_mono(main, auxiliary)

        self.assertEqual(background.size, (560, 192))
        self.assertEqual(set(background.tobytes()), {0, 255})
        self.assertEqual(decoded.tobytes(), background.tobytes())

    def test_font_has_fixed_dual_bank_glyphs(self) -> None:
        font = HIGH_SCORES.build_font()

        self.assertEqual(
            len(font),
            len(HIGH_SCORES.GLYPHS) * HIGH_SCORES.FONT_GLYPH_BYTES,
        )
        self.assertEqual(len(HIGH_SCORES.GLYPHS), 40)
        self.assertEqual(
            set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ .>-"),
            set(HIGH_SCORES.GLYPHS),
        )

    def test_seeded_preview_lines_fit_the_table(self) -> None:
        for index, (name, score) in enumerate(HIGH_SCORES.SEEDED_ROWS):
            line = HIGH_SCORES.sample_line(index, name, score)
            self.assertEqual(len(line), 15)
            self.assertLessEqual(
                (HIGH_SCORES.TABLE_COLUMN + len(line))
                * HIGH_SCORES.FONT_CELL_SIGNALS,
                376,
            )


if __name__ == "__main__":
    unittest.main()
