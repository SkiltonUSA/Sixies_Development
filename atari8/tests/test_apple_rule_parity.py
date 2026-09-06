#!/usr/bin/env python3

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
APPLE = (ROOT / "apple2" / "src" / "main.c").read_text(encoding="ascii")
ATARI = (ROOT / "atari8" / "src" / "rules.s").read_text(encoding="ascii")
GRAPHICS = (ROOT / "atari8" / "src" / "graphics.s").read_text(encoding="ascii")


def c_array(name: str) -> tuple[int, ...]:
    match = re.search(
        rf"static const unsigned char {name}\[.*?\] = \{{(?P<body>.*?)\}};",
        APPLE,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing Apple array: {name}")
    return tuple(int(value) for value in re.findall(r"\d+", match.group("body")))


def asm_array(name: str) -> tuple[int, ...]:
    match = re.search(rf"^{name}:\s*\.byte (?P<body>[^\n]+)", ATARI, re.MULTILINE)
    if match is None:
        raise AssertionError(f"missing Atari array: {name}")
    return tuple(int(value) for value in re.findall(r"\d+", match.group("body")))


class AppleRuleParityTests(unittest.TestCase):
    def test_approved_pair_pool_is_shared_verbatim(self) -> None:
        self.assertEqual(asm_array("pair_first"), c_array("pair_piece_first"))
        self.assertEqual(asm_array("pair_second"), c_array("pair_piece_second"))

    def test_first_generic_callout_pool_is_shared_verbatim(self) -> None:
        self.assertEqual(
            asm_array("first_merge_callouts"),
            c_array("first_merge_effects"),
        )

    def test_piece_frequency_unlocks_and_forced_weighting_match(self) -> None:
        spawn = ATARI.split("spawn_piece:", 1)[1].split(
            "weighted_surrounding_face:", 1
        )[0]
        self.assertRegex(spawn, r"lda #4\s+jsr count_board_value\s+cpx #3")
        self.assertRegex(spawn, r"lda #5\s+jsr count_board_value\s+cpx #4")
        self.assertIn("ldx #3\n    jsr random_mod_x", spawn)
        self.assertIn("jsr weighted_surrounding_face", spawn)
        self.assertIn("ldx #6\n    jsr random_mod_x", spawn)

        rng = ATARI.split("random16:", 1)[1].split("count_board_value:", 1)[0]
        self.assertIn("adc #$B3", rng)
        self.assertIn("adc rng_state+1", rng)
        self.assertIn("adc rng_state+2", rng)
        self.assertIn("adc rng_state+3", rng)
        self.assertIn("and #$7F", rng)
        self.assertIn("ldy #16", rng)

    def test_unlocked_single_mapping_handles_five_without_four(self) -> None:
        spawn = ATARI.split("@normal_single:", 1)[1].split("@store_single:", 1)[0]
        self.assertIn("cpx #3", spawn)
        self.assertIn("lda four_unlocked\n    beq @single_five", spawn)
        self.assertIn("@single_five:\n    lda #5", spawn)
        self.assertIn("@single_four:\n    lda #4", spawn)
        self.assertIn("@base_single:\n    txa\n    clc\n    adc #1", spawn)

    def test_merge_scoring_and_named_outcomes_match(self) -> None:
        resolve = ATARI.split("resolve_at:", 1)[1].split("find_group:", 1)[0]
        score = ATARI.split("score_group:", 1)[1]
        self.assertIn("cmp #4\n    beq @fives", resolve)
        self.assertIn("cmp #5\n    beq @sixies", resolve)
        self.assertIn("cmp #2\n    bcs @awesome", resolve)
        self.assertRegex(score, r"lda group_value\s+cmp #6\s+bne @add")
        self.assertIn("adc #50", score)
        self.assertNotIn("sta score_lo\n    sta score_hi", score)

    def test_diagonal_ripple_uses_apple_faces_five_and_six(self) -> None:
        ripple = GRAPHICS.split("toggle_merge_ripple_step:", 1)[1].split(
            "queue_ripple_xy:", 1
        )[0]
        self.assertIn("lda group_value\n    cmp #5\n    bcc @done", ripple)


if __name__ == "__main__":
    unittest.main()
