#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_high_score_screen.py"
DICE = APPLE2_DIR / "assets" / "high_score_dice_master.ppm"
MASCOT = APPLE2_DIR / "assets" / "high_score_mascot_master.png"
SPEC = importlib.util.spec_from_file_location("generate_high_score_screen", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HIGH_SCORES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HIGH_SCORES)


class GenerateHighScoreScreenTests(unittest.TestCase):
    def test_background_is_round_trip_monochrome_dhgr(self) -> None:
        background = HIGH_SCORES.render_background(DICE, MASCOT)
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

    def test_dice_shadow_is_removed_without_losing_colored_pips(self) -> None:
        source = HIGH_SCORES.Image.open(DICE).convert("RGB")
        dice = HIGH_SCORES.monochrome_dice(DICE)

        shadow = next(
            (x, y)
            for y in range(source.height)
            for x in range(source.width)
            if source.getpixel((x, y)) == (74, 74, 74)
        )
        colored_pip = next(
            (x, y)
            for y in range(source.height)
            for x in range(source.width)
            if source.getpixel((x, y)) == (142, 60, 151)
        )

        self.assertEqual(dice.getpixel((shadow[0] * 2, shadow[1])), 0)
        self.assertEqual(dice.getpixel((colored_pip[0] * 2, colored_pip[1])), 255)

    def test_background_has_no_panel_borders(self) -> None:
        background = HIGH_SCORES.render_background(DICE, MASCOT)

        self.assertEqual(background.getpixel((12, 5)), 0)
        self.assertEqual(background.getpixel((143, 35)), 0)
        self.assertEqual(background.getpixel((391, 43)), 0)
        self.assertEqual(background.getpixel((77, 168)), 0)
        self.assertEqual(background.crop((403, 125, 543, 145)).getbbox(), None)

    def test_mascot_fits_left_of_high_score_table(self) -> None:
        mascot = HIGH_SCORES.monochrome_mascot(MASCOT)
        left, top = HIGH_SCORES.MASCOT_POSITION

        self.assertEqual(mascot.size, HIGH_SCORES.MASCOT_SIZE)
        self.assertEqual(set(mascot.tobytes()), {0, 255})
        self.assertIsNotNone(mascot.getbbox())
        self.assertLessEqual(left + mascot.width, HIGH_SCORES.TABLE_COLUMN * 14)
        self.assertLessEqual(top + mascot.height, 160)


if __name__ == "__main__":
    unittest.main()
