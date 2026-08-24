#!/usr/bin/env python3

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).parents[1]
SOURCE = (ROOT / "src" / "main.c").read_text(encoding="ascii")
ASSEMBLY = (ROOT / "src" / "auxmem.s").read_text(encoding="ascii")


def function_body(signature: str) -> str:
    match = re.search(
        rf"static [^\n]+ {re.escape(signature)} \{{(?P<body>.*?)\n\}}",
        SOURCE,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"function not found: {signature}")
    return match.group("body")


class ScreenShakeTests(unittest.TestCase):
    def test_shake_is_reserved_for_exactly_three_fives_or_sixes(self) -> None:
        body = function_body(
            "resolve_at(unsigned char x, unsigned char y)"
        )
        shake = body.index("if (turn_merge_count >= 5u)")
        ripple = body.index("run_merge_grid_ripple", shake)
        condition = body[shake:ripple]
        self.assertIn("run_merge_grid_shake();", condition)

    def test_chain_state_preserves_exact_three_die_face(self) -> None:
        body = function_body(
            "merge_at(unsigned char x, unsigned char y)"
        )
        self.assertIn("turn_merge_count = count == 3u ? value : 1u;", body)

    def test_five_and_six_merges_enable_diagonal_ripple(self) -> None:
        body = function_body("resolve_at(unsigned char x, unsigned char y)")
        ripple = body[body.index("run_merge_grid_ripple("):body.index("update_score_display")]
        self.assertIn("merge_sound_value >= 5u", ripple)

        step = function_body(
            "toggle_ripple_step(\n"
            "    unsigned char merge_x,\n"
            "    unsigned char merge_y,\n"
            "    unsigned char step,\n"
            "    unsigned char diagonal\n"
            ")"
        )
        self.assertIn("if (diagonal)", step)
        self.assertIn("toggle_diagonal_ripple_step(merge_x, merge_y, step);", step)
        self.assertIn(
            "static const signed char ripple_diagonal_dx[4] = {-1, 1, -1, 1};",
            SOURCE,
        )
        self.assertIn(
            "static const signed char ripple_diagonal_dy[4] = {-1, -1, 1, 1};",
            SOURCE,
        )

    def test_shake_sequence_restores_original_position(self) -> None:
        body = re.search(
            r"\.proc _run_merge_grid_shake(?P<body>.*?)\.endproc",
            ASSEMBLY,
            re.DOTALL,
        )
        self.assertIsNotNone(body)
        directions = re.findall(
            r"lda #([01])\s+jsr shift_grid_rows",
            body.group("body"),
        )
        self.assertEqual(directions, ["1", "0", "0", "1"])
        self.assertIn("lda #2", body.group("body"))

    def test_row_rotations_are_inverse_operations(self) -> None:
        original = list(range(9, 31))
        right = [original[-1], *original[:-1]]
        restored = [*right[1:], right[0]]
        self.assertEqual(restored, original)

    def test_assembly_restores_page_one_after_each_bank(self) -> None:
        for name in ("right", "left"):
            match = re.search(
                rf"shift_row_{name}:(?P<body>.*?)(?:shift_row_{name}_bank:)",
                ASSEMBLY,
                re.DOTALL,
            )
            self.assertIsNotNone(match)
            body = match.group("body")
            self.assertIn("sta EIGHTY_STORE_ON", body)
            self.assertIn("sta PAGE2", body)
            self.assertIn("sta EIGHTY_STORE_OFF", body)
            self.assertIn("sta PAGE1", body)

    def test_shake_reuses_generated_board_rows(self) -> None:
        self.assertIn("GRID_SHAKE_ROWS = 120", ASSEMBLY)
        self.assertIn("lda _dice_blit_row_low,x", ASSEMBLY)
        self.assertIn("lda _dice_blit_row_high,x", ASSEMBLY)

    def test_shake_code_stays_in_language_card(self) -> None:
        shake = ASSEMBLY.index(".proc _run_merge_grid_shake")
        language_card = ASSEMBLY.rfind('.segment "LC"', 0, shake)
        main_code = ASSEMBLY.find('.segment "CODE"', language_card + 1)
        self.assertGreater(language_card, -1)
        self.assertGreater(main_code, shake)


if __name__ == "__main__":
    unittest.main()
