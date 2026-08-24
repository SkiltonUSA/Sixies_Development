#!/usr/bin/env python3

from pathlib import Path
import unittest


SOURCE = (Path(__file__).parents[1] / "src" / "main.c").read_text(encoding="ascii")


def source_between(signature: str, next_signature: str) -> str:
    start = SOURCE.index(signature)
    end = SOURCE.index(next_signature, start)
    return SOURCE[start:end]


class GameInstructionsTests(unittest.TestCase):
    def test_i_opens_instructions_without_changing_game_state(self) -> None:
        game_loop = source_between("static void game_loop(void)", "void main(void)")
        self.assertIn(
            "case 'I':\n                show_game_instructions();\n                continue;",
            game_loop,
        )

    def test_only_space_returns_and_game_page_is_restored(self) -> None:
        body = source_between(
            "static void show_game_instructions(void)",
            "static void high_scores_screen(void)",
        )
        instructions = body.index("instructions_screen();")
        wait = body.index("while (read_input() != ' ')")
        restore = body.index("render_game();")
        drain = body.index("drain_pending_input();")

        self.assertLess(instructions, wait)
        self.assertLess(wait, restore)
        self.assertLess(restore, drain)
        self.assertNotIn("begin_new_game", body)


if __name__ == "__main__":
    unittest.main()
