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
    def test_requested_atari_pair_progression_is_explicit(self) -> None:
        self.assertEqual(asm_array("pair_first"), (1, 1, 2, 3, 3, 3, 3, 4))
        self.assertEqual(asm_array("pair_second"), (2, 3, 3, 1, 2, 3, 4, 5))

    def test_first_generic_callout_pool_is_shared_verbatim(self) -> None:
        self.assertEqual(
            asm_array("first_merge_callouts"),
            c_array("first_merge_effects"),
        )

    def test_piece_frequency_milestones_and_forced_weighting(self) -> None:
        spawn = ATARI.split("spawn_piece:", 1)[1].split(
            "weighted_surrounding_face:", 1
        )[0]
        self.assertNotIn("jsr count_board_value", spawn)
        self.assertIn("ldx #4\n    jsr random_mod_x", spawn)
        self.assertIn("jsr weighted_surrounding_face", spawn)
        self.assertRegex(spawn, r"ldx #15\s+jsr random_mod_x\s+beq @double_three")
        self.assertRegex(spawn, r"lda #5\s+clc\s+adc four_unlocked\s+adc five_unlocked\s+tax\s+jsr random_mod_x")
        self.assertIn("other_pair_index:   .byte 0,1,2,3,4,6,7", ATARI)

        unlocks = ATARI.split("update_piece_unlocks:", 1)[1].split("find_group:", 1)[0]
        self.assertRegex(unlocks, r"lda group_count\s+cmp #4")
        self.assertIn("cmp #4", unlocks)
        self.assertIn("sta four_unlocked", unlocks)
        self.assertIn("cmp #6", unlocks)
        self.assertIn("sta five_unlocked", unlocks)

        rng = ATARI.split("random16:", 1)[1].split("measure_board_pressure:", 1)[0]
        self.assertIn("adc #$B3", rng)
        self.assertIn("adc rng_state+1", rng)
        self.assertIn("adc rng_state+2", rng)
        self.assertIn("adc rng_state+3", rng)
        self.assertIn("and #$7F", rng)
        self.assertIn("ldy #16", rng)

    def test_unlocked_single_mapping_handles_five_without_four(self) -> None:
        spawn = ATARI.split("@normal_single:", 1)[1].split("@store_single:", 1)[0]
        self.assertIn("cpx #3", spawn)
        self.assertIn("lda four_active\n    beq @single_five", spawn)
        self.assertIn("@single_five:\n    lda #5", spawn)
        self.assertIn("@single_four:\n    lda #4", spawn)
        self.assertIn("@base_single:\n    txa\n    clc\n    adc #1", spawn)

    def test_merge_scoring_chain_multiplier_and_named_outcomes(self) -> None:
        resolve = (Path(__file__).resolve().parents[1] / "src/effects.s").read_text()
        score = ATARI.split("score_group:", 1)[1]
        self.assertIn("cmp #4\n    beq @fives", resolve)
        self.assertIn("cmp #5\n    beq @sixies", resolve)
        self.assertIn("cmp #2\n    bcs @awesome", resolve)
        self.assertRegex(score, r"lda group_value\s+cmp #6\s+bne @add")
        self.assertIn("adc #50", score)
        self.assertIn("ldx merge_depth", score)
        self.assertIn("bne @chain_add", score)
        self.assertNotIn("sta score_lo\n    sta score_hi", score)

    def test_diagonal_ripple_uses_apple_faces_five_and_six(self) -> None:
        ripple = GRAPHICS.split("toggle_merge_ripple_step:", 1)[1].split(
            "queue_ripple_xy:", 1
        )[0]
        self.assertIn("lda group_value\n    cmp #5\n    bcc @done", ripple)


if __name__ == "__main__":
    unittest.main()
