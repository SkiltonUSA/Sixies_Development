#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_score_digits.py"
SPEC = importlib.util.spec_from_file_location("generate_score_digits", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class ScoreDigitGenerationTests(unittest.TestCase):
    def test_masks_reproduce_each_glyph_pattern_at_every_position(self) -> None:
        for position in range(GENERATOR.DIGIT_COUNT):
            left = GENERATOR.digit_signal_left(position)
            for pattern in range(8):
                expected = {
                    left + column * GENERATOR.SIGNALS_PER_COLUMN + repeat
                    for column in range(GENERATOR.DIGIT_COLUMNS)
                    if pattern & (4 >> column)
                    for repeat in range(GENERATOR.SIGNALS_PER_COLUMN)
                }
                actual = set()
                for auxiliary in (True, False):
                    offset = GENERATOR.bank_offset(position, auxiliary)
                    mask = GENERATOR.pattern_mask(position, pattern, auxiliary)
                    sequence = offset * 2 + (0 if auxiliary else 1)
                    actual.update(
                        sequence * 7 + bit
                        for bit in range(7)
                        if mask & (1 << bit)
                    )
                self.assertEqual(actual, expected)

    def test_each_digit_uses_at_most_one_byte_per_bank(self) -> None:
        for position in range(GENERATOR.DIGIT_COUNT):
            for auxiliary in (True, False):
                masks = {
                    GENERATOR.pattern_mask(position, pattern, auxiliary)
                    for pattern in range(8)
                }
                self.assertLessEqual(max(masks), 0x7F)

    def test_include_is_deterministic_and_complete(self) -> None:
        output = GENERATOR.generate_include()
        self.assertIn("SCORE_DIGIT_COUNT = 5", output)
        self.assertIn("score_aux_pattern_masks:", output)
        self.assertIn("score_main_pattern_masks:", output)
        self.assertEqual(output, GENERATOR.generate_include())


if __name__ == "__main__":
    unittest.main()
