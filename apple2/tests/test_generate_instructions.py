#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_instructions.py"
SPEC = importlib.util.spec_from_file_location("generate_instructions", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
INSTRUCTIONS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTRUCTIONS)


class InstructionGenerationTests(unittest.TestCase):
    def test_screen_is_title_compatible_monochrome_dhgr(self) -> None:
        image = INSTRUCTIONS.render_instructions()
        main, auxiliary = INSTRUCTIONS.GENERATOR.to_mono_pages(image)
        decoded = INSTRUCTIONS.GENERATOR.A2FM.decode_mono(main, auxiliary)

        self.assertEqual(
            image.size,
            (
                INSTRUCTIONS.GENERATOR.A2FM.SCREEN_WIDTH,
                INSTRUCTIONS.GENERATOR.A2FM.SCREEN_HEIGHT,
            ),
        )
        self.assertEqual(set(image.tobytes()), {0, 255})
        self.assertEqual(decoded.tobytes(), image.tobytes())

    def test_all_instruction_characters_have_glyphs(self) -> None:
        lines = (
            *INSTRUCTIONS.HEADER_LINES,
            *INSTRUCTIONS.RULE_LINES,
            *INSTRUCTIONS.CONTROL_LINES,
            "HOW TO PLAY",
            "CONTROLS",
            "PRESS SPACE OR RETURN TO PLAY",
        )
        self.assertEqual(
            {character for line in lines for character in line} - INSTRUCTIONS.FONT.keys(),
            set(),
        )

    def test_rotation_instructions_use_e_and_q(self) -> None:
        self.assertEqual(
            INSTRUCTIONS.CONTROL_LINES[0],
            "WASD OR ARROWS MOVE   Q OR E ROTATE",
        )

    def test_controls_include_sound_toggle(self) -> None:
        self.assertEqual(INSTRUCTIONS.CONTROL_LINES[2], "[M] TOGGLES SOUND")
        self.assertIn("[", INSTRUCTIONS.FONT)
        self.assertIn("]", INSTRUCTIONS.FONT)


if __name__ == "__main__":
    unittest.main()
