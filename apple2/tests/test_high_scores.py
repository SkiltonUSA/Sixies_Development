#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_high_scores.py"
SOURCE = (APPLE2_DIR / "src" / "main.c").read_text(encoding="ascii")
MAKEFILE = (APPLE2_DIR / "Makefile").read_text(encoding="ascii")
PACKAGER = (APPLE2_DIR / "scripts" / "package_disk.sh").read_text(encoding="ascii")
RUNNER = (APPLE2_DIR / "scripts" / "run-emulator.sh").read_text(encoding="ascii")
SPEC = importlib.util.spec_from_file_location("generate_high_scores", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class HighScoreTests(unittest.TestCase):
    def test_initial_table_has_ten_empty_versioned_entries(self) -> None:
        table = GENERATOR.build_table()
        self.assertEqual(len(table), 56)
        self.assertEqual(table[:5], b"SIXH\x01")
        self.assertEqual(table[5], sum(table[6:]) & 0xFF)
        for index in range(10):
            offset = 6 + index * 5
            self.assertEqual(table[offset : offset + 5], b"---\x00\x00")

    def test_runtime_reuses_transfer_buffer_instead_of_adding_table_bss(self) -> None:
        self.assertIn(
            "return dhgr_transfer_buffer + HIGH_SCORE_DATA_OFFSET",
            SOURCE,
        )
        self.assertNotRegex(SOURCE, r"static unsigned char high_scores\[")

    def test_game_over_loads_sorts_saves_and_displays_scores(self) -> None:
        for call in (
            "load_high_scores();",
            "rank = high_score_rank();",
            "enter_high_score(rank);",
            "show_high_scores(rank);",
        ):
            self.assertIn(call, SOURCE)
        self.assertIn('open("HISCORE", O_WRONLY | O_TRUNC)', SOURCE)
        self.assertIn("HIGH_SCORE_COUNT 10u", SOURCE)

    def test_high_score_file_is_built_and_packaged(self) -> None:
        self.assertIn("HIGH_SCORE_FILE := $(ASSET_DIR)/HISCORE", MAKEFILE)
        self.assertIn("MERGESTAR HISCORE", PACKAGER)

    def test_emulator_runner_preserves_saved_scores(self) -> None:
        self.assertIn('-g "$RUN_DISK" HISCORE "$high_score_backup"', RUNNER)
        self.assertIn('-d "$RUN_DISK" HISCORE', RUNNER)
        self.assertIn('-p "$RUN_DISK" HISCORE bin', RUNNER)
        self.assertLess(RUNNER.index('-g "$RUN_DISK"'), RUNNER.index('cp "$DISK_IMAGE"'))
        self.assertGreater(RUNNER.index('-p "$RUN_DISK"'), RUNNER.index('cp "$DISK_IMAGE"'))


if __name__ == "__main__":
    unittest.main()
