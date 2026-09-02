from pathlib import Path
import re
import unittest


ATARI = Path(__file__).resolve().parents[1]


class BuildContractTests(unittest.TestCase):
    def test_xex_has_run_vector_segment(self):
        data = (ATARI / "build" / "sixies.xex").read_bytes()
        self.assertEqual(data[:2], b"\xff\xff")
        self.assertIn(b"\xe0\x02\xe1\x02", data)

    def test_apple_rule_tables_and_bonus_are_explicit(self):
        rules = (ATARI / "src" / "rules.s").read_text()
        self.assertIn("pair_first:         .byte 1,1,2,2,3,3", rules)
        self.assertIn("pair_second:        .byte 2,3,3,4,3,4", rules)
        self.assertRegex(rules, r"cmp #6\s+bne @add\s+clc\s+lda score_delta_lo\s+adc #50")
        self.assertIn("jsr resolve_at", rules)

    def test_hires_and_128k_paths_are_present(self):
        graphics = (ATARI / "src" / "graphics.s").read_text()
        main = (ATARI / "src" / "main.s").read_text()
        self.assertIn(".byte $4F, <SCREEN, >SCREEN", graphics)
        self.assertIn("sta PORTB", main)
        self.assertIn("cache_title_128", main)
        self.assertIn("jsr show_presents", main)
        self.assertIn("game_over_asset", graphics)
        self.assertEqual(re.findall(r"cmp #128", main).count("cmp #128"), 2)

    def test_banking_code_and_saved_state_stay_outside_the_bank_window(self):
        labels = (ATARI / "build" / "sixies.lbl").read_text().splitlines()
        addresses = {}
        for line in labels:
            match = re.fullmatch(r"al ([0-9A-Fa-f]{6}) \.([A-Za-z0-9_]+)", line)
            if match:
                addresses[match.group(2)] = int(match.group(1), 16)

        for name in (
            "detect_memory",
            "cache_title_128",
            "restore_title_128",
            "copy_screen_to_bank",
            "copy_bank_to_screen",
            "video_update_begin",
            "video_update_end",
        ):
            self.assertIn(name, addresses)
            self.assertLess(addresses[name], 0x4000, name)

        for name in (
            "zp_saved_portb",
            "zp_saved_main_4000",
            "zp_saved_main_4001",
            "zp_detected_kb",
        ):
            self.assertIn(name, addresses)
            self.assertLess(addresses[name], 0x0100, name)

    def test_wasd_keys_map_to_four_movement_actions(self):
        hardware = (ATARI / "src" / "hardware.inc").read_text()
        main = (ATARI / "src" / "main.s").read_text()
        expected = {
            "A": ("left", "ACTION_LEFT"),
            "D": ("right", "ACTION_RIGHT"),
            "W": ("up", "ACTION_UP"),
            "S": ("down", "ACTION_DOWN"),
        }
        for key, (branch, action) in expected.items():
            self.assertRegex(hardware, rf"KEY_{key}\s+=\s+\$[0-9A-F]{{2}}")
            self.assertRegex(main, rf"cmp #KEY_{key}\s+beq @{branch}")
            self.assertRegex(main, rf"@{branch}:\s+lda #{action}\s+rts")
        self.assertIn("and #KEY_CODE_MASK", main)
        self.assertIn("lda STICK1", main)
        self.assertIn("lda STRIG1", main)
        self.assertRegex(main, r"@title_ready:\s+jsr arm_input")
        self.assertRegex(main, r"arm_input:\s+lda #CH_NONE\s+sta CH\s+lda #1\s+sta input_latch")
        launcher = (ATARI / "scripts" / "run-emulator.sh").read_text()
        self.assertIn("-no-kbdjoy0", launcher)
        self.assertIn("-kbdjoy1", launcher)
        self.assertNotRegex(launcher, r"(?<!-no)-kbdjoy0")


if __name__ == "__main__":
    unittest.main()
