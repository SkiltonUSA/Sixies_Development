#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import re
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SOURCE = (APPLE2_DIR / "src" / "main.c").read_text(encoding="ascii")
ASSEMBLY = (APPLE2_DIR / "src" / "auxmem.s").read_text(encoding="ascii")


class FooterSeparatorTests(unittest.TestCase):
    def test_runtime_draws_separator_after_loading_grid(self) -> None:
        render = re.search(
            r"static void render_game\(void\) \{(?P<body>.*?)\n\}",
            SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(render)
        body = render.group("body")
        self.assertLess(body.index("set_double_hires(0);"), body.index("draw_footer_separator();"))

    def test_assembly_draws_two_banked_solid_scanlines(self) -> None:
        self.assertIn(".export _draw_footer_separator", ASSEMBLY)
        routine = re.search(
            r"\.proc _draw_footer_separator(?P<body>.*?)\.endproc",
            ASSEMBLY,
            re.DOTALL,
        )
        self.assertIsNotNone(routine)
        body = routine.group("body")
        self.assertIn("sta EIGHTY_STORE_ON", body)
        self.assertIn("sta PAGE2", body)
        self.assertIn("sta EIGHTY_STORE_OFF", body)
        self.assertIn("sta PAGE1", body)
        self.assertIn("sta $2E50,x", body)
        self.assertIn("sta $3250,x", body)


if __name__ == "__main__":
    unittest.main()
