from pathlib import Path
import random
import sys
import unittest

from runtime6502 import Machine

ATARI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ATARI / "scripts"))
from generate_assets import pack_rle, unpack_rle


class CompiledRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.m = Machine()

    def test_sound_survives_busy_polling_and_expires_after_two_ticks(self):
        m = self.m
        m.call("sound_init")
        m.memory[0x14] = 254
        m.call("play_move_sound")
        for _ in range(100):
            m.call("sound_update")
        self.assertEqual(m.get("sound_frames"), 2)
        self.assertEqual(m.memory[0xD201], 0xA6)
        m.memory[0x14] = 255
        m.call("sound_update")
        self.assertEqual(m.get("sound_frames"), 1)
        m.memory[0x14] = 0
        m.call("sound_update")
        self.assertEqual(m.memory[0xD201], 0)

    def test_all_effects_and_spiral_are_frame_clocked_and_mute_silences(self):
        m = self.m
        m.call("sound_init")
        for name, arg, duration in (("play_move_sound", 0, 2),
                                   ("play_rotate_sound", 0, 4),
                                   ("play_place_sound", 0, 5),
                                   ("play_invalid_sound", 0, 10),
                                   ("play_merge_sound", 4, 16),
                                   ("play_spiral_sound", 0x98, 2)):
            m.call(name, a=arg)
            for _ in range(duration):
                self.assertNotEqual(m.memory[0xD201], 0, name)
                m.memory[0x14] = (m.memory[0x14] + 1) & 255
                m.call("sound_update")
            self.assertEqual(m.memory[0xD201], 0, name)
        m.call("play_move_sound")
        m.call("sound_toggle")
        self.assertEqual(m.memory[0xD201:0xD208:2], [0]*4)

    def test_wasd_modifiers_rotation_and_release_debug_disabled(self):
        for key, action in ((0x3F, 1), (0x3A, 2), (0x2E, 3), (0x3E, 4),
                            (0x2F, 13), (0x2A, 5), (0x21, 6), (0x38, 14)):
            for modifier in (0, 64, 128, 192):
                if key | modifier == 255:  # OS reserves $FF for no buffered key
                    continue
                self.m.memory[0x2FC] = key | modifier
                self.assertEqual(self.m.call("poll_action"), action)
        self.m.memory[0x2FC] = 0x22
        self.assertEqual(self.m.call("poll_action"), 0)

    def test_joystick_chord_never_places_on_release_on_either_port(self):
        for port in range(2):
            m = Machine()
            m.set("gameplay_input", 1)
            stick, fire = 0x278 + port, 0x284 + port
            m.memory[fire] = 0
            self.assertEqual(m.call("poll_action"), 0)
            m.memory[stick] = 7
            self.assertEqual(m.call("poll_action"), 5)
            self.assertEqual(m.call("poll_action"), 0)
            m.memory[stick] = 15
            self.assertEqual(m.call("poll_action"), 0)
            m.memory[stick] = 11
            self.assertEqual(m.call("poll_action"), 13)
            m.memory[fire] = 1
            self.assertEqual(m.call("poll_action"), 0)
            m.memory[stick] = 15
            m.call("poll_action")
            m.memory[fire] = 0
            self.assertEqual(m.call("poll_action"), 0)
            m.memory[fire] = 1
            self.assertEqual(m.call("poll_action"), 6)

    def test_menu_fire_remains_immediate_and_arm_suppresses_held_fire(self):
        m = self.m
        m.memory[0x284] = 0
        m.call("arm_input")
        self.assertEqual(m.call("poll_action"), 0)
        m.memory[0x284] = 1
        m.call("poll_action")
        m.memory[0x284] = 0
        self.assertEqual(m.call("poll_action"), 6)
        self.assertEqual(m.call("poll_action"), 0)

    def test_animation_polls_without_clobbering_scratch_or_queuing_placement(self):
        m = self.m
        m.set("gameplay_input", 1)
        m.set("zp_temp", 123)
        m.memory[0x2FC] = 0x3F
        m.call("wait_frames", a=2, x=45, y=67, ticks=True)
        self.assertEqual(m.get("queued_action"), 1)
        self.assertEqual(m.get("zp_temp"), 123)
        self.assertEqual((m.cpu.x, m.cpu.y), (45, 67))
        self.assertEqual(m.call("wait_action"), 1)
        m.memory[0x2FC] = 0x21
        m.call("service_animation_input")
        self.assertEqual(m.get("queued_action"), 0)

    def test_compiled_decoder_matches_every_lossless_asset(self):
        m = self.m
        for name in ("title_logo", "presents", "instructions", "game_over", "game_grid"):
            file = ATARI / "build/assets" / f"{name}.rle"
            packed = file.read_bytes()
            m.memory[0x400:0x400 + len(packed)] = packed
            m.set("zp_asset", 0)
            m.memory[m.symbols["zp_asset"] + 1] = 4
            m.memory[0x7FFF] = 0xA5
            m.memory[0x9F00] = 0x5A
            m.call("unpack_screen_rle")
            self.assertEqual(bytes(m.memory[0x8000:0x9F00]), unpack_rle(packed), file.name)
            self.assertEqual(m.memory[0x7FFF], 0xA5)
            self.assertEqual(m.memory[0x9F00], 0x5A)

    def test_backreferences_round_trip_overlaps_runs_and_literal_boundaries(self):
        rng = random.Random(17)
        for data in (b"AB"*3968, bytes(7936), bytes(range(256))*31,
                     rng.randbytes(7936)):
            self.assertEqual(unpack_rle(pack_rle(data)), data)
        for malformed in (b"\x80", b"\x80\x00\x05", b"\x80\x01\x05",
                          b"\x00A\x80\x01\x00"):
            with self.assertRaises(ValueError):
                unpack_rle(malformed)

    def test_callout_restores_exact_pixels_at_all_25_origins(self):
        m = self.m
        background = random.Random(12).randbytes(7936)
        for cell in range(25):
            m.memory[0x8000:0x9F00] = background
            m.set("active_index", cell)
            m.set("text_index", cell % 10)
            m.call("show_callout")
            self.assertNotEqual(bytes(m.memory[0x8000:0x9E60]), background[:0x1E60])
            m.call("hide_callout")
            self.assertEqual(bytes(m.memory[0x8000:0x9E60]), background[:0x1E60], cell)

    def test_merge_award_is_formatted_over_each_cell_and_restores_pixels(self):
        m = self.m
        for award, expected in ((1, b"    +1\0"), (15, b"   +15\0"),
                                (296, b"  +296\0"), (65535, b"+65535\0")):
            m.set("score_delta_lo", award & 255)
            m.set("score_delta_hi", award >> 8)
            m.call("format_merge_score")
            self.assertEqual(bytes(m.region("merge_score_string", 7)), expected)

        background = random.Random(29).randbytes(7936)
        m.set("score_delta_lo", 40)
        m.set("score_delta_hi", 0)
        for cell in range(25):
            m.memory[0x8000:0x9F00] = background
            m.set("active_index", cell)
            m.call("show_merge_score")
            self.assertEqual((m.get("blit_x"), m.get("blit_y")), (2, 28))
            self.assertNotEqual(bytes(m.memory[0x8000:0x9E60]), background[:0x1E60])
            m.call("hide_callout")
            self.assertEqual(bytes(m.memory[0x8000:0x9E60]), background[:0x1E60], cell)

    def test_chain_multiplier_badge_shoots_and_restores_every_pixel(self):
        m = self.m
        background = random.Random(46).randbytes(7936)
        for cell, depth, expected in ((0, 2, b"2X\0"),
                                      (12, 3, b"3X\0"),
                                      (24, 10, b"9X\0")):
            m.memory[0x8000:0x9F00] = background
            m.set("active_index", cell)
            m.set("merge_depth", depth)
            m.call("shoot_chain_multiplier", ticks=True)
            self.assertEqual(bytes(m.region("chain_badge_string", 3)), expected)
            self.assertEqual(bytes(m.memory[0x8000:0x9E60]), background[:0x1E60], cell)

    def test_chain_reaction_art_appears_below_sidebar_dice_then_clears(self):
        m = self.m
        m.memory[0x8000:0x9F00] = [0] * 0x1F00
        m.call("show_chain_reaction_sidebar")
        self.assertEqual((m.get("blit_x"), m.get("blit_y")), (30, 120))
        rendered = bytearray()
        for row in range(120, 152):
            address = 0x9000 + (row - 100) * 40
            rendered.extend(m.memory[address + 30:address + 40])
        self.assertEqual(bytes(rendered), bytes(m.region("chain_reaction_asset", 320)))
        m.call("hide_chain_reaction_sidebar")
        self.assertFalse(any(rendered_byte for row in range(120, 152)
                             for rendered_byte in m.memory[
                                 0x9000 + (row - 100) * 40 + 30:
                                 0x9000 + (row - 100) * 40 + 40
                             ]))

    def test_chain_banner_timer_does_not_block_gameplay(self):
        m = self.m

        def banner_visible():
            return any(value for row in range(120, 152)
                       for value in m.memory[
                           0x9000 + (row - 100) * 40 + 30:
                           0x9000 + (row - 100) * 40 + 40
                       ])

        m.memory[0x8000:0x9F00] = [0] * 0x1F00
        m.call("show_chain_reaction_sidebar")
        m.memory[0x14] = 200
        m.call("arm_chain_reaction_sidebar")
        self.assertEqual(m.get("chain_banner_frames"), 60)
        self.assertTrue(banner_visible())

        # Presentation pages pause the gameplay-only timer.
        m.memory[0x14] = 201
        m.call("update_chain_reaction_sidebar")
        self.assertEqual(m.get("chain_banner_frames"), 60)

        # A movement action is returned immediately while the timer advances.
        m.set("gameplay_input", 1)
        m.memory[0x14] = 202
        m.memory[0x2FC] = 0x3F  # A / left
        self.assertEqual(m.call("wait_action"), 1)
        self.assertEqual(m.get("chain_banner_frames"), 59)
        self.assertTrue(banner_visible())

        for frame in range(58):
            m.memory[0x14] = (203 + frame) & 255
            m.call("update_chain_reaction_sidebar")
        self.assertEqual(m.get("chain_banner_frames"), 1)
        self.assertTrue(banner_visible())
        m.memory[0x14] = (203 + 58) & 255
        m.call("update_chain_reaction_sidebar")
        self.assertEqual(m.get("chain_banner_frames"), 0)
        self.assertFalse(banner_visible())

    def rules_only(self):
        self.m.stub("redraw_group_cells", "redraw_score_digits", "play_merge_sound",
                    "flash_six_clear", "run_merge_grid_ripple", "show_merge_star",
                    "show_callout", "hide_callout", "wait_frames")

    def test_chain_and_six_clear_score_with_apple_16_bit_wrap(self):
        m = self.m
        self.rules_only()
        board = [0]*25
        for i in (0, 1, 2): board[i] = 1
        for i in (5, 10): board[i] = 2
        m.put("board", board)
        m.call("resolve_at", a=0)
        self.assertEqual(m.region("board", 25), [3] + [0]*24)
        self.assertEqual(m.get("score_lo"), 15)
        m.put("board", [6, 6, 6]+[0]*22)
        m.set("score_lo", 250)
        m.set("score_hi", 255)
        m.set("merge_depth", 0)
        m.call("resolve_at", a=0)
        self.assertEqual(m.region("board", 25), [0]*25)
        self.assertEqual((m.get("score_hi"), m.get("score_lo")), (0, 62))

    def test_pair_boundaries_and_occupied_partner_reject_without_mutation(self):
        m = self.m
        m.set("piece_count", 2)
        for x, y, orientation in ((4, 2, 0), (2, 4, 1), (0, 2, 2), (2, 0, 3)):
            m.set("cursor_x", x)
            m.set("cursor_y", y)
            m.set("orientation", orientation)
            m.call("placement_valid")
            self.assertFalse(m.cpu.p & 1)
            self.assertEqual(m.region("board", 25), [0]*25)
        m.set("cursor_x", 2)
        m.set("cursor_y", 2)
        m.set("orientation", 0)
        board = [0]*25
        board[13] = 4
        m.put("board", board)
        m.call("placement_valid")
        self.assertFalse(m.cpu.p & 1)
        self.assertEqual(m.region("board", 25), board)

    def test_pair_resolves_both_origins_without_losing_second_index(self):
        m = self.m
        self.rules_only()
        m.stub("spawn_piece")
        board = [0]*25
        board[5] = board[10] = 1
        board[6] = board[11] = 4
        m.put("board", board)
        m.set("piece_count", 2)
        m.set("piece_a", 1)
        m.set("piece_b", 4)
        m.call("place_current_piece")
        self.assertTrue(m.cpu.p & 1)
        self.assertEqual(m.region("board", 25), [2, 5]+[0]*23)
        self.assertEqual(m.get("score_lo"), 27)

    def test_chain_multiplier_includes_group_size_and_six_bonus(self):
        m = self.m
        # Invoke the scoring boundary directly to isolate ×1..×4 arithmetic.
        cases = ((1, 3, 1, 3), (2, 4, 2, 16), (5, 3, 3, 45), (6, 4, 4, 296))
        for face, count, depth, expected in cases:
            m.set("group_value", face)
            m.set("group_count", count)
            m.set("merge_depth", depth)
            m.set("score_lo", 0)
            m.set("score_hi", 0)
            m.call("score_group")
            score = m.get("score_lo") | (m.get("score_hi") << 8)
            self.assertEqual(score, expected)

    def test_real_merge_effects_preserve_result_and_accept_mute(self):
        m = self.m
        m.call("new_game")
        m.call("render_game")
        m.put("board", [4,4,4]+[0]*22)
        m.set("gameplay_input", 1)
        m.set("sound_enabled", 1)
        m.memory[0x2FC] = 0x25  # M during the first effect frame
        m.call("resolve_at", a=0, ticks=True)
        self.assertEqual(m.region("board", 25), [5]+[0]*24)
        self.assertEqual(m.get("score_lo"), 12)
        self.assertEqual(m.get("sound_enabled"), 0)

    def test_sidebar_is_clean_and_confirmation_leaves_header_untouched(self):
        from PIL import Image
        m = self.m
        m.call("new_game")
        m.call("render_game")
        header = m.memory[0x8000:0x8000 + 24*40]
        # The right sidebar remains blank below the next-piece preview.
        for y in range(90, 166):
            address = 0x8000 + y*40 if y < 100 else 0x9000 + (y-100)*40
            row = m.memory[address:address+40]
            self.assertEqual(row[30:40], [0]*10, y)
        # Diagnostic previews are rendered from the linked 6502 instructions.
        output = ATARI / "build/previews"
        output.mkdir(parents=True, exist_ok=True)
        def snapshot(name):
            raw = bytes(m.memory[0x8000:0x8FA0] + m.memory[0x9000:0x9E60])
            Image.frombytes("1", (320,192), raw).save(output / name)
        snapshot("runtime-game.png")
        m.call("show_chain_reaction_sidebar")
        snapshot("runtime-chain-reaction.png")
        m.call("hide_chain_reaction_sidebar")
        m.call("show_new_game_confirm")
        self.assertEqual(m.memory[0x8000:0x8000 + 24*40], header)
        snapshot("runtime-confirm.png")

    def test_sidebar_dice_match_all_hover_orientations(self):
        m = self.m
        m.set("piece_count", 2)
        m.set("piece_a", 1)
        m.set("piece_b", 6)

        def rect(x, y, width, height):
            pixels = bytearray()
            for row in range(y, y + height):
                address = (0x8000 + row*40 if row < 100
                           else 0x9000 + (row-100)*40)
                pixels.extend(m.memory[address+x:address+x+width])
            return bytes(pixels)

        def render(orientation):
            m.memory[0x8000:0x9F00] = [0] * 0x1F00
            m.set("orientation", orientation)
            m.call("draw_piece_sidebar")

        render(0)  # A then B, pointing right
        die_a = rect(31, 64, 4, 24)
        die_b = rect(35, 64, 4, 24)
        self.assertTrue(any(die_a))
        self.assertTrue(any(die_b))
        self.assertFalse(any(rect(31, 88, 8, 24)))

        render(2)  # B then A, pointing left
        self.assertEqual(rect(31, 64, 4, 24), die_b)
        self.assertEqual(rect(35, 64, 4, 24), die_a)

        render(1)  # A over B, pointing down
        self.assertEqual(rect(33, 64, 4, 24), die_a)
        self.assertEqual(rect(33, 88, 4, 24), die_b)

        render(3)  # B over A, pointing up
        self.assertEqual(rect(33, 64, 4, 24), die_b)
        self.assertEqual(rect(33, 88, 4, 24), die_a)

    def test_forced_single_on_isolated_empty_cells(self):
        m = self.m
        board = [1]*25
        board[0] = board[24] = 0
        m.put("board", board)
        m.put("rng_state", [1, 0, 1, 0])
        for _ in range(50):
            m.call("spawn_piece")
            self.assertEqual(m.get("piece_count"), 1)
            self.assertEqual(m.get("game_over"), 0)

    def test_dealt_piece_pool_expands_only_at_requested_milestones(self):
        stages = (
            (0, 0,
             {(1,2), (1,3), (2,3), (3,1), (3,2), (3,3)},
             {1,2,3}),
            (1, 0,
             {(1,2), (1,3), (2,3), (3,1), (3,2), (3,3), (3,4)},
             {1,2,3,4}),
            (1, 1,
             {(1,2), (1,3), (2,3), (3,1), (3,2), (3,3), (3,4), (4,5)},
             {1,2,3,4,5}),
        )
        for four, five, expected_pairs, expected_singles in stages:
            m = Machine()
            m.put("rng_state", [1, 0, 1, 0])
            m.set("four_unlocked", four)
            m.set("five_unlocked", five)
            pairs, singles, pair_count, double_three = set(), set(), 0, 0
            for _ in range(1800):
                m.call("spawn_piece")
                if m.get("piece_count") == 2:
                    pair_count += 1
                    pair = (m.get("piece_a"), m.get("piece_b"))
                    pairs.add(pair)
                    double_three += pair == (3,3)
                else:
                    singles.add(m.get("piece_a"))
            self.assertEqual(pairs, expected_pairs)
            self.assertEqual(singles, expected_singles)
            self.assertGreater(pair_count, 1260)
            self.assertLess(pair_count, 1440)
            self.assertGreater(double_three, 60)
            self.assertLess(double_three, 120)

    @staticmethod
    def sample_deals(board, count=2400, four=0, five=0):
        from collections import Counter
        m = Machine()
        m.put("board", board)
        m.put("rng_state", [1, 0, 1, 0])
        m.set("four_unlocked", four)
        m.set("five_unlocked", five)
        pieces, faces = Counter(), Counter()
        for _ in range(count):
            m.call("spawn_piece")
            if m.get("piece_count") == 2:
                piece = (m.get("piece_a"), m.get("piece_b"))
                pieces[piece] += 1
                faces.update(piece)
            else:
                piece = (m.get("piece_a"),)
                pieces[piece] += 1
                faces.update(piece)
        return pieces, faces

    def test_four_pressure_boosts_fours_and_suppresses_ones_and_twos(self):
        normal_pieces, normal_faces = self.sample_deals([0]*25)
        pressure_pieces, pressure_faces = self.sample_deals([4,4,4,4]+[0]*21)
        total = 2400
        four_deals = pressure_pieces[(3,4)] + pressure_pieces[(4,)]
        self.assertGreater(four_deals, int(total * 0.45))
        self.assertLess(four_deals, int(total * 0.55))
        self.assertGreater(pressure_pieces[(3,4)], int(total * 0.31))
        self.assertLess(pressure_pieces[(3,4)], int(total * 0.39))
        self.assertGreater(pressure_pieces[(4,)], int(total * 0.12))
        self.assertLess(pressure_pieces[(4,)], int(total * 0.18))
        for face in (1, 2):
            self.assertLess(pressure_faces[face], normal_faces[face] * 0.65)

    def test_crowded_board_progressively_deals_matching_singles(self):
        match_rates = []
        pair_rates = []
        for occupied in (15, 18, 22, 24):
            pieces, _ = self.sample_deals([2]*occupied + [0]*(25-occupied), 1600)
            match_rates.append(pieces[(2,)] / 1600)
            pair_rates.append(sum(value for key, value in pieces.items() if len(key) == 2) / 1600)
        self.assertLess(match_rates[0], 0.12)
        self.assertGreater(match_rates[1], 0.45)
        self.assertGreater(match_rates[2], 0.70)
        self.assertGreater(match_rates[3], 0.99)
        self.assertGreater(pair_rates[0], pair_rates[1])
        self.assertGreater(pair_rates[1], pair_rates[2])
        self.assertEqual(pair_rates[3], 0)

    def test_four_plus_four_and_six_merge_milestones_persist(self):
        m = self.m
        self.rules_only()
        m.put("board", [4,4,4]+[0]*22)
        m.call("resolve_at", a=0)
        self.assertEqual(m.get("four_unlocked"), 0)
        m.put("board", [4,4,4,4]+[0]*21)
        m.call("resolve_at", a=0)
        self.assertEqual(m.get("four_unlocked"), 1)
        self.assertEqual(m.get("five_unlocked"), 0)
        m.put("board", [6,6,6]+[0]*22)
        m.call("resolve_at", a=0)
        self.assertEqual(m.get("five_unlocked"), 0)
        m.put("board", [6,6,6,6]+[0]*21)
        m.call("resolve_at", a=0)
        self.assertEqual(m.get("five_unlocked"), 1)
        m.put("board", [0]*25)
        m.call("spawn_piece")
        self.assertEqual((m.get("four_unlocked"), m.get("five_unlocked")), (1,1))

    def test_new_game_resets_deal_milestones(self):
        m = self.m
        m.set("four_unlocked", 1)
        m.set("five_unlocked", 1)
        m.call("new_game")
        self.assertEqual((m.get("four_unlocked"), m.get("five_unlocked")), (0,0))

    def test_score_insertion_keeps_ties_older_and_drops_eleventh(self):
        m = self.m
        entries = []
        for i in range(10):
            entries.extend([65+i]*3 + [100-i*10, 0])
        m.put("high_score_sector", [83,73,88,72,1,0] + entries)
        m.set("score_lo", 80)
        self.assertEqual(m.call("high_score_rank"), 3)
        m.set("high_score_ranked", 3)
        m.call("high_score_insert")
        data = m.region("high_score_sector", 56)[6:]
        self.assertEqual(data[15:20], [65,65,65,80,0])
        self.assertEqual(data[20:25], entries[15:20])
        self.assertEqual(data[45:50], entries[40:45])

    def test_save_failure_retains_table_and_retry_success_clears_status(self):
        m = self.m
        m.put("high_score_sector", [83,73,88,72,1,0]+[65,65,65,123,0]*10)
        original = m.region("high_score_sector", 56)
        for status, expected in ((144, 2), (1, 1)):
            # OS SIO stub sets DSTATS, just as the real OS entry point does.
            m.memory[0xE459:0xE45F] = [0xA9, status, 0x8D, 3, 3, 0x60]
            m.call("high_scores_save")
            self.assertEqual(m.get("high_score_save_status"), expected)
            self.assertEqual(bool(m.cpu.p & 1), expected == 2)
            self.assertEqual(m.region("high_score_sector", 56)[6:], original[6:])

    def test_credits_respond_before_music_reveal(self):
        m = self.m
        m.call("show_credits")
        self.assertEqual(m.get("credits_reveal_frames"), 120)
        self.assertEqual(m.get("credits_line_index"), 2)
        def press_fire(machine):
            if machine.memory[0x14] == 10:
                machine.memory[0x284] = 0
        self.assertEqual(m.call("wait_attract_seconds", a=11, ticks=True, hook=press_fire), 6)
        self.assertEqual(m.get("credits_line_index"), 2)
        self.assertTrue(m.cpu.p & 1)

    def test_credits_reveal_once_and_complete_interval(self):
        m = self.m
        m.call("show_credits")
        m.call("wait_attract_seconds", a=3, ticks=True)
        self.assertEqual(m.get("credits_reveal_frames"), 0)
        self.assertEqual(m.get("credits_line_index"), 4)
        self.assertFalse(m.cpu.p & 1)

    def test_reduced_flashing_does_not_modify_framebuffer_or_palette(self):
        m = self.m
        m.set("reduced_flashing", 1)
        before = m.memory[0x8000:0xA000]
        for routine in ("flash_six_clear", "run_merge_grid_ripple", "run_game_start_spiral"):
            m.call(routine, limit=50)
        self.assertEqual(m.memory[0x8000:0xA000], before)
        self.assertEqual(m.memory[0xD016:0xD01B], [0]*5)

    def test_starting_hover_dice_wait_until_spiral_restores_center(self):
        m = self.m
        m.call("new_game")
        m.set("piece_visible", 0)
        m.call("render_game")

        def framebuffer():
            return bytes(m.memory[0x8000:0x8FA0] + m.memory[0x9000:0x9E60])

        hidden = framebuffer()
        # The independent next-piece panel is already available to the player.
        self.assertTrue(any(value for row in range(64, 88)
                            for value in m.memory[0x8000 + row*40 + 31:
                                                  0x8000 + row*40 + 39]))
        m.call("run_game_start_spiral", ticks=True)
        self.assertEqual(framebuffer(), hidden)
        m.set("piece_visible", 1)
        m.call("draw_piece_preview")
        self.assertNotEqual(framebuffer(), hidden)


if __name__ == "__main__":
    unittest.main()
