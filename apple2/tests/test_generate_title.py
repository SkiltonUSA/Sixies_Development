#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_title.py"
MASTER = APPLE2_DIR / "assets" / "title_dhgr_mono_master.a2fm"
SPEC = importlib.util.spec_from_file_location("generate_title", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
TITLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TITLE)


class GenerateTitleTests(unittest.TestCase):
    def test_prompt_is_rendered_without_changing_a2fm_size(self) -> None:
        source = MASTER.read_bytes()
        main_page, auxiliary_page, image = TITLE.render_title(source)

        self.assertEqual(len(auxiliary_page + main_page), len(source))
        self.assertNotEqual(auxiliary_page + main_page, source)
        self.assertGreater(
            sum(
                image.getpixel((x, y)) != 0
                for y in range(TITLE.PROMPT_Y, TITLE.PROMPT_Y + 7)
                for x in range(TITLE.A2FM.SCREEN_WIDTH)
            ),
            0,
        )

    def test_prompt_font_contains_every_character(self) -> None:
        self.assertEqual(
            set(TITLE.PROMPT) - TITLE.INSTRUCTIONS.FONT.keys(),
            set(),
        )


if __name__ == "__main__":
    unittest.main()
