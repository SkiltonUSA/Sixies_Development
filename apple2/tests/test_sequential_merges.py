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

    def test_named_effects_describe_the_value_created(self) -> None:
        body = function_body("merge_at(unsigned char x, unsigned char y)")
        fives_condition = body.index("if (value == 4)")
        fives_effect = body.index("merge_effect_index = MERGE_EFFECT_FIVES;")
        sixies_condition = body.index("else if (value == 5)")
        self.assertIn("merge_effect_index = MERGE_EFFECT_SIXIES;", body)
        self.assertLess(fives_condition, fives_effect)
        self.assertLess(fives_effect, sixies_condition)

    def test_awesome_is_reserved_for_later_merges_in_the_turn(self) -> None:
        body = function_body("merge_at(unsigned char x, unsigned char y)")
        self.assertIn("else if (turn_merge_count != 0)", body)
        self.assertIn("merge_effect_index = MERGE_EFFECT_AWESOME;", body)
        self.assertIn("merge_effect_index = first_merge_effects[rand() % 7u];", body)
        self.assertIn("turn_merge_count = count == 3u ? value : 1u;", body)

        resolve = function_body(
            "resolve_merges(unsigned char first_x, unsigned char first_y, "
            "unsigned char second_x, unsigned char second_y)"
        )
        reset = resolve.index("turn_merge_count = 0;")
        first = resolve.index("resolve_at(first_x, first_y);")
        second = resolve.index("resolve_at(second_x, second_y);")
        self.assertLess(reset, first)
        self.assertLess(first, second)

    def test_first_merge_pool_excludes_reserved_words(self) -> None:
        match = re.search(
            r"static const unsigned char first_merge_effects\[7\] = \{"
            r"(?P<body>.*?)\n\};",
            SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        self.assertEqual(match.group("body").strip(), "1, 2, 4, 6, 7, 8, 9,")

    def test_new_current_piece_is_generated_after_merge_resolution(self) -> None:
        body = function_body("game_loop(void)")
        resolve = body.index(
            "resolve_merges(placed_x1, placed_y1, placed_x2, placed_y2);"
        )
        advance = body.index("advance_piece();", resolve)
        preview = body.index("draw_current_piece_preview();", advance)
        self.assertLess(resolve, advance)
        self.assertLess(advance, preview)

    def test_next_piece_queue_and_sidebar_preview_are_removed(self) -> None:
        self.assertNotIn("next_piece_", SOURCE)
        sidebar = function_body("draw_piece_sidebar(void)")
        self.assertIn("draw_sidebar_die(1, piece_count == 2 ? piece_a : 0);", sidebar)
        self.assertIn("draw_sidebar_die(2, piece_count == 2 ? piece_b : piece_a);", sidebar)
        self.assertNotIn("draw_sidebar_die(0", sidebar)
        self.assertNotIn("draw_sidebar_die(3", sidebar)


if __name__ == "__main__":
    unittest.main()
