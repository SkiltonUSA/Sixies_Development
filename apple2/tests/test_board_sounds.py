#!/usr/bin/env python3

from pathlib import Path
import re
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SOURCE = (APPLE2_DIR / "src" / "main.c").read_text(encoding="ascii")
ASSEMBLY = (APPLE2_DIR / "src" / "auxmem.s").read_text(encoding="ascii")
INSTRUCTIONS = (APPLE2_DIR / "scripts" / "generate_instructions.py").read_text(
    encoding="ascii"
)


def game_loop_source() -> str:
    start = SOURCE.index("static void game_loop(void)")
    end = SOURCE.index("void main(void)", start)
    return SOURCE[start:end]


class BoardSoundTests(unittest.TestCase):
    def test_speaker_routines_reproduce_c64_effect_mapping(self) -> None:
        for symbol in (
            "_play_move_sound",
            "_play_rotate_sound",
            "_play_place_sound",
            "_play_invalid_placement_sound",
            "_play_merge_sound",
        ):
            self.assertIn(f".export {symbol}", ASSEMBLY)
        self.assertIn("SPEAKER = $C030", ASSEMBLY)
        self.assertIn("bit SPEAKER", ASSEMBLY)
        self.assertRegex(
            ASSEMBLY,
            r"_play_rotate_sound:\n_play_place_sound:\n"
            r"    lda #60\n    ldx #24",
        )

    def test_invalid_sound_uses_descending_pitch_periods(self) -> None:
        match = re.search(
            r"\.proc _play_invalid_placement_sound(?P<body>.*?)\.endproc",
            ASSEMBLY,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        periods = tuple(int(value) for value in re.findall(r"lda #(\d+)", match.group("body")))
        self.assertEqual(periods, (100, 135, 180, 250))

    def test_merge_sounds_map_each_consumed_value(self) -> None:
        self.assertIn("static unsigned char merge_sound_value;", SOURCE)
        merge = SOURCE[SOURCE.index("static unsigned char merge_at("):]
        self.assertIn("merge_sound_value = value;", merge)
        self.assertIn("play_merge_sound(merge_sound_value);", merge)
        self.assertIn("merge_note_delays:", ASSEMBLY)
        self.assertIn("merge_note_transitions:", ASSEMBLY)
        self.assertIn("cmp #6\n    beq merge_six_noise", ASSEMBLY)
        self.assertIn("eor #$b8", ASSEMBLY)

    def test_merge_sound_starts_after_redraw_before_visual_effects(self) -> None:
        start = SOURCE.index("static void resolve_at(unsigned char x, unsigned char y)")
        end = SOURCE.index("static void resolve_merges(", start)
        resolve = SOURCE[start:end]
        redraw = resolve.index("redraw_board_changes();")
        sound = resolve.index("play_merge_sound(merge_sound_value);")
        ripple = resolve.index("run_merge_grid_ripple(")
        self.assertLess(redraw, sound)
        self.assertLess(sound, ripple)

    def test_valid_board_sounds_follow_visual_updates(self) -> None:
        game_loop = game_loop_source()
        placement = game_loop.index("if (placement_changed)")
        redraw = game_loop.index("redraw_board_changes();", placement)
        place_sound = game_loop.index("play_place_sound();", redraw)
        resolve = game_loop.index("resolve_merges(", place_sound)
        preview = game_loop.index("else if (preview_changed)", resolve)
        preview_redraw = game_loop.index("redraw_preview_transition(", preview)
        rotate_sound = game_loop.index("play_rotate_sound();", preview_redraw)
        move_sound = game_loop.index("play_move_sound();", rotate_sound)

        self.assertLess(redraw, place_sound)
        self.assertLess(place_sound, resolve)
        self.assertLess(preview_redraw, rotate_sound)
        self.assertLess(preview_redraw, move_sound)

    def test_failed_placement_plays_bonk_without_board_redraw(self) -> None:
        game_loop = game_loop_source()
        placement_call = game_loop.index("placement_changed = place_piece(")
        invalid_check = game_loop.index("if (!placement_changed)", placement_call)
        invalid_sound = game_loop.index("play_invalid_placement_sound();", invalid_check)
        placement_branch = game_loop.index("if (placement_changed)", invalid_sound)

        self.assertLess(placement_call, invalid_check)
        self.assertLess(invalid_check, invalid_sound)
        self.assertLess(invalid_sound, placement_branch)

    def test_m_toggles_sound_without_moving_the_piece(self) -> None:
        self.assertIn("unsigned char sound_enabled = 1;", SOURCE)
        self.assertIn("static void toggle_sound(void)", SOURCE)
        self.assertIn("sound_enabled = (unsigned char) !sound_enabled;", SOURCE)
        self.assertIn("case 'M':\n                toggle_sound();\n                continue;", SOURCE)
        self.assertIn('cprintf("[M] TOGGLES SOUND");', SOURCE)
        self.assertIn('"[M] SOUND   [I] INSTRUCTIONS"', INSTRUCTIONS)
        self.assertIn("ldy _sound_enabled", ASSEMBLY)
        self.assertIn("beq speaker_tone_done", ASSEMBLY)


if __name__ == "__main__":
    unittest.main()
