#!/usr/bin/env python3

from pathlib import Path
import unittest


SOURCE = (Path(__file__).parents[1] / "src" / "main.c").read_text(encoding="ascii")


class RotationControlTests(unittest.TestCase):
    def test_gameplay_uses_e_and_q_without_r(self) -> None:
        self.assertIn("case 'E':\n            case 'Q':", SOURCE)
        self.assertNotIn("case 'R':", SOURCE)

    def test_instruction_fallback_uses_e_and_q(self) -> None:
        self.assertIn('cprintf("WASD MOVE  Q OR E ROTATE");', SOURCE)
        self.assertNotIn("Q OR R ROTATE", SOURCE)


if __name__ == "__main__":
    unittest.main()
