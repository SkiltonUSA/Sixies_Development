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


class HoverFlashTests(unittest.TestCase):
    def test_flash_uses_vbl_timer_while_polling_input(self) -> None:
        self.assertIn("#define HOVER_FLASH_FRAMES 18u", SOURCE)
        body = function_body("wait_for_game_input(void)")
        self.assertIn("while (!kbhit())", body)
        self.assertIn("wait_animation_frames(1);", body)
        self.assertIn("if (frames == HOVER_FLASH_FRAMES)", body)
        self.assertIn("preview_inverted = (unsigned char) !preview_inverted;", body)

    def test_keypress_restores_visible_preview(self) -> None:
        body = function_body("wait_for_game_input(void)")
        restore = body.index("if (preview_inverted)")
        read = body.index("return read_input();")
        self.assertIn("invert_current_piece_preview();", body[restore:read])
        self.assertLess(restore, read)

    def test_flash_is_limited_to_preview_cells(self) -> None:
        body = function_body("invert_current_piece_preview(void)")
        self.assertIn("if (dhgr_grid_active)", body)
        self.assertIn("invert_dhgr_board_tile(x1, y1);", body)
        self.assertIn("invert_dhgr_board_tile(x2, y2);", body)
        self.assertNotIn("set_double_hires", body)
        self.assertNotIn("activate_soft_switch", body)
        self.assertNotIn("draw_piece_sidebar", body)
        self.assertNotIn("render_game", body)

    def test_preview_preserves_existing_face_and_hatch_rules(self) -> None:
        body = function_body("draw_current_piece_preview(void)")
        self.assertIn("if (board_value(x1, y1) == 0)", body)
        self.assertIn("if (board_value(x2, y2) == 0)", body)
        self.assertIn("draw_invalid_mark(x1, y1);", body)
        self.assertIn("draw_die(x1, y1, piece_a, 1);", body)
        self.assertNotIn("dhgr_transfer_buffer", body)
        self.assertNotIn("invert_dhgr_board_tile", body)

    def test_aux_inversion_restores_page_one(self) -> None:
        assembly = (Path(__file__).parents[1] / "src" / "auxmem.s").read_text(
            encoding="ascii"
        )
        body = re.search(
            r"\.proc _invert_dhgr_tile_aux(?P<body>.*?)\.endproc",
            assembly,
            re.DOTALL,
        )
        self.assertIsNotNone(body)
        aux_body = body.group("body")
        self.assertIn("sta EIGHTY_STORE_ON", aux_body)
        self.assertIn("sta PAGE2", aux_body)
        self.assertIn("sta EIGHTY_STORE_OFF", aux_body)
        self.assertIn("sta PAGE1", aux_body)
        self.assertNotIn("RAMWRT_AUX", aux_body)

    def test_game_loop_uses_flashing_input_wait(self) -> None:
        body = function_body("game_loop(void)")
        self.assertIn("ch = wait_for_game_input();", body)


if __name__ == "__main__":
    unittest.main()
