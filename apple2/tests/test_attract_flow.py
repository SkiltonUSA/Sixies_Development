#!/usr/bin/env python3

from pathlib import Path
import re
import unittest


SOURCE = (Path(__file__).parents[1] / "src" / "main.c").read_text(encoding="ascii")


class AttractFlowTests(unittest.TestCase):
    def test_attract_timing_constants_are_explicit(self) -> None:
        self.assertIn("#define ATTRACT_SCREEN_SECONDS 5u", SOURCE)
        self.assertIn("#define INITIAL_TITLE_SECONDS 10u", SOURCE)
        self.assertIn("#define NTSC_FRAMES_PER_SECOND 60u", SOURCE)

    def test_attract_loop_uses_initial_and_rotating_sequence(self) -> None:
        match = re.search(
            r"static void startup_attract_loop\(void\) \{(?P<body>.*?)\n\}",
            SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        body = match.group("body")

        initial_title = body.index("INITIAL_TITLE_SECONDS")
        loop_start = body.index("while (1)")
        instructions = body.index("instructions_screen();", loop_start)
        high_scores = body.index("high_scores_screen();", instructions)
        presents = body.index("presents_screen();", high_scores)
        title = body.index("title_screen();", presents)
        self.assertLess(initial_title, loop_start)
        self.assertLess(instructions, high_scores)
        self.assertLess(high_scores, presents)
        self.assertLess(presents, title)

    def test_attract_high_scores_reload_saved_table_without_rank_marker(self) -> None:
        match = re.search(
            r"static void high_scores_screen\(void\) \{(?P<body>.*?)\n\}",
            SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        body = match.group("body")
        self.assertIn("load_high_scores();", body)
        self.assertIn("show_high_scores(HIGH_SCORE_COUNT);", body)

    def test_timed_wait_polls_for_start_keys(self) -> None:
        match = re.search(
            r"static unsigned char wait_for_start_or_timeout\(unsigned frames\) "
            r"\{(?P<body>.*?)\n\}",
            SOURCE,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        body = match.group("body")
        self.assertIn("kbhit()", body)
        self.assertIn("ch == ' ' || ch == CH_ENTER || ch == 'N'", body)
        self.assertIn("wait_animation_frames(1);", body)


if __name__ == "__main__":
    unittest.main()
