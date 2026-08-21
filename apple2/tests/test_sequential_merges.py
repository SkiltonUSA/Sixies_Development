#!/usr/bin/env python3

from pathlib import Path
import re
import unittest


SOURCE = (Path(__file__).parents[1] / "src" / "main.c").read_text(encoding="ascii")


def function_body(signature: str) -> str:
    match = re.search(
        rf"static [^\n]+ {re.escape(signature)} \{{(?P<body>.*?)\n\}}",
        SOURCE,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"function not found: {signature}")
    return match.group("body")


class SequentialMergeTests(unittest.TestCase):
    def test_each_merge_redraws_and_presents_before_next_iteration(self) -> None:
        body = function_body("resolve_at(unsigned char x, unsigned char y)")
        snapshot = body.index("memcpy(placement_board_before, board, sizeof(board));")
        merge = body.index("merge_at(x, y)")
        redraw = body.index("redraw_board_changes();")
        ripple = body.index("run_merge_grid_ripple(merge_effect_x, merge_effect_y);")
        score = body.index("update_score_display();")
        callout = body.index("show_merge_flash(merge_effect_index);")
        self.assertLess(snapshot, merge)
        self.assertLess(merge, redraw)
        self.assertLess(redraw, ripple)
        self.assertLess(ripple, score)
        self.assertLess(score, callout)

    def test_each_merge_selects_its_own_effect(self) -> None:
        body = function_body("merge_at(unsigned char x, unsigned char y)")
        self.assertIn("merge_effect_index = MERGE_EFFECT_SIXIES;", body)
        self.assertIn("merge_effect_index = MERGE_EFFECT_FIVES;", body)
        self.assertIn("merge_effect_index = general_merge_effects[rand() % 8u];", body)
        self.assertNotIn("merge_effect_pending", body)

    def test_piece_queue_advances_after_merge_resolution(self) -> None:
        body = function_body("game_loop(void)")
        resolve = body.index(
            "resolve_merges(placed_x1, placed_y1, placed_x2, placed_y2);"
        )
        advance = body.index("advance_piece_queue();", resolve)
        preview = body.index("draw_current_piece_preview();", advance)
        self.assertLess(resolve, advance)
        self.assertLess(advance, preview)


if __name__ == "__main__":
    unittest.main()
