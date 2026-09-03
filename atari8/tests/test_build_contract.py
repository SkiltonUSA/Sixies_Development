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

    def test_period_key_fills_board_and_uses_normal_game_over_flow(self):
        hardware = (ATARI / "src" / "hardware.inc").read_text()
        main = (ATARI / "src" / "main.s").read_text()
        rules = (ATARI / "src" / "rules.s").read_text()
        self.assertRegex(hardware, r"KEY_PERIOD\s+=\s+\$22")
        self.assertIn("cmp #KEY_PERIOD", main)
        self.assertRegex(main, r"@debug_fill:\s+lda #ACTION_DEBUG_FILL\s+rts")
        self.assertRegex(
            main,
            r"debug_game_over:\s+jsr debug_fill_board\s+jsr render_game\s+jmp game_loop",
        )
        self.assertRegex(
            rules,
            re.compile(
                r"debug_fill_board:.*?sta board,x.*?sta piece_visible.*?sta game_over",
                re.DOTALL,
            ),
        )

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

    def test_credits_page_is_reachable_from_title(self):
        hardware = (ATARI / "src" / "hardware.inc").read_text()
        main = (ATARI / "src" / "main.s").read_text()
        credits = (ATARI / "src" / "credits.s").read_text()
        self.assertRegex(hardware, r"KEY_C\s+=\s+\$12")
        self.assertIn("jsr wait_for_title", main)
        self.assertRegex(main, r"cmp #KEY_C\s+beq @credits")
        self.assertRegex(
            credits,
            re.compile(
                r"wait_for_title:.*?jsr show_credits.*?jsr show_title",
                re.DOTALL,
            ),
        )
        self.assertIn('.asciiz "CREDITS"', credits)
        self.assertIn('.asciiz "DSKILTON"', credits)
        self.assertIn('.asciiz "ETERNITY 1"', credits)
        self.assertIn('.asciiz "PRZEMYSLAW"', credits)
        self.assertIn('.asciiz "LEWANDOWSKI"', credits)
        self.assertIn('.asciiz "STUDIO 313 GAMES"', credits)
        self.assertIn("jsr draw_sidebar_die", credits)
        self.assertIn("lda SKSTAT", credits)
        self.assertIn("lda KBCODE", credits)
        self.assertRegex(
            credits,
            re.compile(
                r"wait_for_title:.*?lda #5.*?jsr wait_attract_seconds"
                r".*?jsr show_high_scores.*?lda #5.*?jsr wait_attract_seconds"
                r".*?jsr show_credits.*?lda #11.*?jsr wait_attract_seconds"
                r".*?jsr show_title.*?jmp @title",
                re.DOTALL,
            ),
        )
        self.assertIn("jsr sound_update", (ATARI / "src" / "graphics.s").read_text())

    def test_game_footer_is_drawn_in_assembly(self):
        graphics = (ATARI / "src" / "graphics.s").read_text()
        self.assertIn('text_new_game:      .asciiz "[N]EW GAME"', graphics)
        self.assertIn('text_instructions:  .asciiz "[I]NSTRUCTIONS"', graphics)
        self.assertIn("draw_game_footer:", graphics)
        self.assertIn("draw_footer_box:", graphics)
        render = graphics.split("render_game:", 1)[1].split("show_title:", 1)[0]
        self.assertIn("jsr draw_game_footer", render)
        self.assertNotIn("text_sixies", render)
        self.assertNotIn("text_next", graphics)

    def test_gameplay_uses_gold_logo_and_cyan_hires_grid(self):
        graphics = (ATARI / "src" / "graphics.s").read_text()
        hardware = (ATARI / "src" / "hardware.inc").read_text()
        self.assertIn("GAME_GOLD_HUE = $10", graphics)
        self.assertIn("GAME_CYAN_HUE = $A0", graphics)
        self.assertIn("GAME_CYAN_BRIGHT = $AE", graphics)
        self.assertIn("VDSLST          = $0200", hardware)
        self.assertIn("WSYNC           = $D40A", hardware)
        self.assertEqual(graphics.count(".byte $8F"), 2)
        render = graphics.split("render_game:", 1)[1].split("show_title:", 1)[0]
        self.assertIn("lda #GAME_GOLD_HUE", render)
        self.assertIn("sta COLOR2", render)
        self.assertIn("sta COLPF2", render)
        self.assertIn("jmp arm_gameplay_dli", render)
        dli = graphics.split("color_band_dli:", 1)[1].split("arm_gameplay_dli:", 1)[0]
        self.assertIn("lda VCOUNT", dli)
        self.assertIn("cmp #60", dli)
        self.assertIn("lda dli_middle_hue", dli)
        self.assertIn("lda #GAME_GOLD_HUE", dli)
        self.assertIn("sta WSYNC", dli)
        self.assertIn("sta COLPF2", dli)
        self.assertIn("rti", dli)
        arm_dli = graphics.split("arm_gameplay_dli:", 1)[1].split(
            '.segment "CODE"', 1
        )[0]
        self.assertIn("lda #GAME_CYAN_HUE", arm_dli)
        self.assertIn("sta dli_middle_hue", arm_dli)
        self.assertIn("#<color_band_dli", arm_dli)
        self.assertIn("lda #$C0", arm_dli)
        self.assertIn("sta NMIEN", arm_dli)
        update = graphics.split("video_update_begin:", 1)[1].split(
            "video_update_end:", 1
        )[0]
        self.assertIn("lda #HIRES_WHITE", update)
        self.assertIn("sta COLOR2", update)
        self.assertIn("sta COLPF2", update)

        launcher = (ATARI / "scripts" / "run-emulator.sh").read_text()
        self.assertIn("-ntsc-filter-preset rgb", launcher)
        self.assertNotIn("-ntsc-filter-preset monochrome", launcher)

    def test_instructions_follow_title_before_gameplay(self):
        main = (ATARI / "src" / "main.s").read_text()
        graphics = (ATARI / "src" / "graphics.s").read_text()
        startup = main.split("@title_ready:", 1)[1].split("begin_game:", 1)[0]
        sequence = (
            "jsr wait_for_title",
            "jsr sound_stop_music",
            "jsr show_instructions",
            "jsr arm_input",
            "jsr wait_for_start",
        )
        position = 0
        for instruction in sequence:
            position = startup.index(instruction, position) + len(instruction)

        instruction_page = graphics.split("show_instructions:", 1)[1].split(
            "show_new_game_confirm:", 1
        )[0]
        self.assertIn("lda #GAME_GOLD_HUE", instruction_page)
        self.assertIn("jmp arm_instructions_dli", instruction_page)
        instruction_arm = graphics.split("arm_instructions_dli:", 1)[1].split(
            "arm_color_band_dli:", 1
        )[0]
        self.assertIn("lda #0", instruction_arm)

    def test_title_music_uses_compressed_sid2sapr_softbass(self):
        player = (ATARI / "src" / "sid_music.s").read_text()
        config = (ATARI / "cfg" / "sixies.cfg").read_text()
        stream = ATARI / "assets" / "music" / "eternity_1_intro_softbass.lz16"

        self.assertEqual(stream.stat().st_size, 399)
        self.assertIn(
            '.incbin "assets/music/eternity_1_intro_softbass.lz16"', player
        )
        self.assertRegex(player, r"inc sapr_ratediv\s+lda sapr_ratediv\s+cmp #6")
        self.assertNotIn("jmp (sapr_saved_vimirq)", player)
        self.assertRegex(player, r"sta sapr_saved_pokmsk\s+lda #0\s+sta POKMSK")
        self.assertRegex(player, r"bcc sapr_irq_timer2\s+jmp sapr_irq_timer4")
        self.assertIn("sta sapr_saved_pokmsk", player)
        self.assertIn("sta sapr_saved_vimirq", player)
        self.assertIn('MUSICBSS: load = HIRAM,  type = bss', config)

    def test_game_over_flows_through_persistent_high_scores(self):
        main = (ATARI / "src" / "main.s").read_text()
        scores = (ATARI / "src" / "high_scores.s").read_text()
        package = (ATARI / "scripts" / "package_disk.sh").read_text()

        game_over = main.split("game_finished:", 1)[1].split("wait_for_start:", 1)[0]
        for instruction in (
            "jsr show_game_over",
            "jsr wait_for_start",
            "jsr high_scores_after_game",
            "jsr wait_for_start",
            "jmp begin_game",
        ):
            self.assertIn(instruction, game_over)
        self.assertIn("HIGH_SCORE_COUNT       = 10", scores)
        self.assertIn("HIGH_SCORE_SECTOR      = 720", scores)
        self.assertIn("high_score_edit_initials:", scores)
        self.assertIn("high_score_key_letters:", scores)
        self.assertIn("high_scores_save:", scores)
        self.assertIn('high_score_title:          .asciiz "SIXIES HIGH SCORES"', scores)
        self.assertIn("preserve_high_scores.py", package)

    def test_flat_title_uses_dedicated_art_region_and_clear_prompt_rows(self):
        graphics = (ATARI / "src" / "graphics.s").read_text()
        title = graphics.split("show_title:", 1)[1].split("show_presents:", 1)[0]
        self.assertIn("lda #154", title)
        self.assertIn("lda #176", title)

    def test_merge_animation_uses_dirty_updates_without_full_screen_blanking(self):
        main = (ATARI / "src" / "main.s").read_text()
        rules = (ATARI / "src" / "rules.s").read_text()
        graphics = (ATARI / "src" / "graphics.s").read_text()
        resolve = rules.split("resolve_at:", 1)[1].split("find_group:", 1)[0]
        self.assertNotIn("jsr render_game", resolve)
        self.assertIn("jsr redraw_group_cells", resolve)
        self.assertIn("jsr redraw_score_digits", resolve)
        self.assertIn("jsr run_merge_grid_ripple", resolve)
        self.assertIn("jsr flash_six_clear", resolve)
        self.assertEqual(resolve.count("jsr show_merge_star"), 4)
        self.assertEqual(resolve.count("jsr show_callout"), 1)
        self.assertEqual(resolve.count("jsr hide_callout"), 1)
        self.assertIn("CALLOUT_FRAMES = 30", rules)
        self.assertIn("lda #CALLOUT_FRAMES", resolve)
        place = main.split("place_piece:", 1)[1].split("toggle_audio:", 1)[0]
        self.assertIn("jsr refresh_turn_display", place)
        self.assertNotIn("jsr render_game", place)
        callout = graphics.split("show_callout:", 1)[1].split("show_merge_star:", 1)[0]
        self.assertIn("jsr save_callout_underlay", callout)
        self.assertIn("jsr clear_bitmap_rect", callout)
        self.assertIn("jmp blit_or", callout)
        self.assertIn("ldx active_index", callout)
        self.assertIn("lda cell_x_bytes,x", callout)
        self.assertIn("lda cell_y_pixels,x", callout)
        self.assertIn("sbc #3", callout)
        self.assertIn("lda #10", callout)
        self.assertIn("lda #20", callout)
        self.assertIn("CALLOUT_UNDERLAY = $9E60", graphics)
        self.assertIn("restore_callout_underlay:", graphics)

    def test_merge_grid_boxes_ripple_inward_and_restore(self):
        graphics = (ATARI / "src" / "graphics.s").read_text()
        ripple = graphics.split("run_merge_grid_ripple:", 1)[1]
        self.assertIn("jsr toggle_merge_ripple_step", ripple)
        self.assertIn("lda #2", ripple)
        self.assertIn("jsr wait_frames", ripple)
        self.assertIn("cmp #5", ripple)
        self.assertIn("queue_ripple_xy:", ripple)
        self.assertIn("cmp group_queue,x", ripple)
        invert = ripple.split("invert_ripple_cell:", 1)[1]
        for mask in ("eor #$0F", "eor #$FF", "eor #$F0"):
            self.assertIn(mask, invert)

    def test_special_merge_feedback_is_tied_to_exact_outcomes(self):
        rules = (ATARI / "src" / "rules.s").read_text()
        graphics = (ATARI / "src" / "graphics.s").read_text()
        resolve = rules.split("resolve_at:", 1)[1].split("find_group:", 1)[0]

        self.assertIn("sta merged_count", resolve)
        self.assertIn("regular_callouts:   .byte 0,1,2,4,6,7,8,9", rules)
        selection = resolve.split("; Reserve the named outcome callouts", 1)[1]
        self.assertIn("lda merged_count\n    cmp #3", selection)
        self.assertIn("cmp #4\n    beq @fives", selection)
        self.assertIn("cmp #5\n    beq @sixies", selection)

        ripple = graphics.split("toggle_merge_ripple_step:", 1)[1].split(
            "queue_ripple_xy:", 1
        )[0]
        self.assertIn("lda group_value\n    cmp #4", ripple)
        for corner in (
            "lda ripple_left\n    ldx ripple_top",
            "lda ripple_right\n    ldx ripple_top",
            "lda ripple_left\n    ldx ripple_bottom",
            "lda ripple_right\n    ldx ripple_bottom",
        ):
            self.assertIn(corner, ripple)

        flash = graphics.split("flash_six_clear:", 1)[1].split(
            "save_callout_underlay:", 1
        )[0]
        self.assertIn("sta COLBK", flash)
        self.assertIn("sta COLPF1", flash)
        self.assertIn("lda #5\n    jsr wait_frames", flash)


if __name__ == "__main__":
    unittest.main()
