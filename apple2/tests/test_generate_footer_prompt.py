#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_footer_prompt.py"
SPEC = importlib.util.spec_from_file_location("generate_footer_prompt", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class FooterPromptGenerationTests(unittest.TestCase):
    def test_masks_reproduce_every_prompt_signal(self) -> None:
        auxiliary_masks = GENERATOR.bank_masks(True)
        main_masks = GENERATOR.bank_masks(False)
        auxiliary_bytes = GENERATOR.bank_byte_count(True)
        main_bytes = GENERATOR.bank_byte_count(False)

        for row in range(GENERATOR.PROMPT_ROWS):
            actual = set()
            for auxiliary, masks, byte_count in (
                (True, auxiliary_masks, auxiliary_bytes),
                (False, main_masks, main_bytes),
            ):
                offset = GENERATOR.bank_offset(auxiliary)
                parity = 0 if auxiliary else 1
                for index, mask in enumerate(
                    masks[row * byte_count : (row + 1) * byte_count]
                ):
                    sequence = (offset + index) * 2 + parity
                    actual.update(
                        sequence * 7 + bit
                        for bit in range(7)
                        if mask & (1 << bit)
                    )
            self.assertEqual(actual, GENERATOR.lit_signals(row))

    def test_prompt_fits_the_empty_footer(self) -> None:
        self.assertEqual(GENERATOR.PROMPT, "ARE YOU SURE [Y/N]?")
        self.assertGreaterEqual(GENERATOR.PROMPT_LEFT, 138)
        self.assertLess(GENERATOR.PROMPT_RIGHT, 560)
        self.assertEqual(GENERATOR.bank_byte_count(True), 11)
        self.assertEqual(GENERATOR.bank_byte_count(False), 11)

    def test_include_is_deterministic(self) -> None:
        output = GENERATOR.generate_include()
        self.assertIn("FOOTER_PROMPT_ROWS = 5", output)
        self.assertIn("footer_prompt_aux_masks:", output)
        self.assertIn("footer_prompt_main_masks:", output)
        self.assertEqual(output, GENERATOR.generate_include())


if __name__ == "__main__":
    unittest.main()
