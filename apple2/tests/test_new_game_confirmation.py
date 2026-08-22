#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import re
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SOURCE = (APPLE2_DIR / "src" / "main.c").read_text(encoding="ascii")
ASSEMBLY = (APPLE2_DIR / "src" / "auxmem.s").read_text(encoding="ascii")


class NewGameConfirmationTests(unittest.TestCase):
    def test_only_y_confirms_and_n_restores_current_game(self) -> None:
        confirmation = re.search(
            r"static unsigned char confirm_new_game\(void\) \{(?P<body>.*?)\n\}",
            SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(confirmation)
        body = confirmation.group("body")
        self.assertEqual(body.count("xor_new_game_prompt();"), 2)
        self.assertIn("ch != 'Y' && ch != 'N'", body)
        self.assertIn("if (ch == 'N')", body)
        self.assertIn("while (quiet_frames < 3u)", body)
        self.assertIn("quiet_frames = 0;", body)
        self.assertIn("return 0;", body)
        self.assertIn("return 1;", body)

    def test_game_loop_requires_confirmation_before_reset(self) -> None:
        self.assertIn(
            "if (confirm_new_game()) {\n                    begin_new_game();\n                }",
            SOURCE,
        )

    def test_prompt_blitter_is_xor_based_and_banked(self) -> None:
        routine = re.search(
            r"\.proc _xor_new_game_prompt(?P<body>.*?)\.endproc",
            ASSEMBLY,
            re.DOTALL,
        )
        self.assertIsNotNone(routine)
        body = routine.group("body")
        self.assertIn("sta EIGHTY_STORE_ON", body)
        self.assertIn("sta PAGE2", body)
        self.assertIn("sta EIGHTY_STORE_OFF", body)
        self.assertIn("sta PAGE1", body)
        self.assertIn("jsr xor_footer_prompt_bank", body)


if __name__ == "__main__":
    unittest.main()
