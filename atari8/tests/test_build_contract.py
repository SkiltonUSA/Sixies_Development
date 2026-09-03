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
        self.assertIn("game_grid_asset", graphics)
        self.assertRegex(
            graphics,
            r"render_game:\s+jsr video_update_begin\s+lda #<game_grid_asset[\s\S]*?jsr unpack_screen_rle",
        )
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

        display_start = addresses["display_list"]
        display_end = addresses["screen_row_lo"]
        self.assertEqual(display_start & 0x3FF, 0)
        self.assertEqual(display_start >> 10, (display_end - 1) >> 10)

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

    def test_cursor_motion_uses_dirty_cell_redraws(self):
        main = (ATARI / "src" / "main.s").read_text()
        graphics = (ATARI / "src" / "graphics.s").read_text()
        for start, end in (
            ("move_left:", "move_right:"),
            ("move_right:", "move_up:"),
            ("move_up:", "move_down:"),
            ("move_down:", "rotate_piece:"),
            ("rotate_piece:", "place_piece:"),
        ):
            block = main.split(start, 1)[1].split(end, 1)[0]
            self.assertIn("jsr erase_piece_preview", block, start)
            self.assertIn("jsr draw_piece_preview", block, start)
            self.assertNotIn("jsr render_game", block, start)
        self.assertIn("restore_cell_under_preview:", graphics)
        self.assertRegex(graphics, r"and #\$F0\s+sta \(zp_screen\),y")
        self.assertRegex(graphics, r"and #\$0F\s+sta \(zp_screen\),y")

    def test_occupied_hover_uses_a_distinct_shaded_overlay(self):
        graphics = (ATARI / "src" / "graphics.s").read_text()
        self.assertIn('occupied_asset:     .incbin "build/assets/occupied.bin"', graphics)
        preview = graphics.split("draw_preview_at_cell:", 1)[1].split(
            "draw_piece_preview:", 1
        )[0]
        self.assertIn("lda board,x", preview)
        self.assertIn("jmp draw_occupied_at_cell", preview)
        self.assertIn("jmp draw_invalid_at_cell", preview)
        self.assertIn("lda preview_show_x", preview)
        invalid = graphics.split("draw_invalid_at_cell:", 1)[1].split(
            "clear_cell_interior:", 1
        )[0]
        self.assertIn("jmp blit_clear", invalid)
        subtractive = graphics.split("blit_clear:", 1)[1].split("blit_xor:", 1)[0]
        self.assertIn("eor #$FF", subtractive)
        self.assertIn("and (zp_screen),y", subtractive)
        occupied = graphics.split("draw_occupied_at_cell:", 1)[1].split(
            "draw_board_dice:", 1
        )[0]
        self.assertIn("jsr clear_cell_interior", occupied)
        piece_preview = graphics.split("draw_piece_preview:", 1)[1].split(
            "draw_mascot:", 1
        )[0]
        self.assertIn("sta preview_show_x", piece_preview)
        self.assertIn("bne @hide_x", piece_preview)
        self.assertRegex(piece_preview, r"@hide_x:\s+lda #0\s+sta preview_show_x")

    def test_game_footer_is_drawn_in_assembly(self):
        graphics = (ATARI / "src" / "graphics.s").read_text()
        self.assertIn('text_new_game:      .asciiz "[N]EW GAME"', graphics)
        self.assertIn('text_instructions:  .asciiz "[I]NSTRUCTIONS"', graphics)
        self.assertIn("draw_game_footer:", graphics)
        self.assertIn("draw_footer_box:", graphics)
        render = graphics.split("render_game:", 1)[1].split("show_title:", 1)[0]
        self.assertIn("jsr draw_game_footer", render)

    def test_instructions_follow_title_before_gameplay(self):
        main = (ATARI / "src" / "main.s").read_text()
        startup = main.split("@title_ready:", 1)[1].split("begin_game:", 1)[0]
        sequence = (
            "jsr wait_for_start",
            "jsr sound_stop_music",
            "jsr show_instructions",
            "jsr arm_input",
            "jsr wait_for_start",
        )
        position = 0
        for instruction in sequence:
            position = startup.index(instruction, position) + len(instruction)

    def test_merge_animation_uses_dirty_updates_without_full_screen_blanking(self):
        main = (ATARI / "src" / "main.s").read_text()
        rules = (ATARI / "src" / "rules.s").read_text()
        graphics = (ATARI / "src" / "graphics.s").read_text()
        resolve = rules.split("resolve_at:", 1)[1].split("find_group:", 1)[0]
        self.assertNotIn("jsr render_game", resolve)
        self.assertIn("jsr redraw_group_cells", resolve)
        self.assertIn("jsr redraw_score_digits", resolve)
        self.assertEqual(resolve.count("jsr show_merge_star"), 4)
        self.assertEqual(resolve.count("jsr show_callout"), 2)
        place = main.split("place_piece:", 1)[1].split("toggle_audio:", 1)[0]
        self.assertIn("jsr refresh_turn_display", place)
        self.assertNotIn("jsr render_game", place)
        callout = graphics.split("show_callout:", 1)[1].split("show_merge_star:", 1)[0]
        self.assertIn("jmp blit_xor", callout)


if __name__ == "__main__":
    unittest.main()
