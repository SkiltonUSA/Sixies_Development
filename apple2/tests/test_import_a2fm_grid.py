#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

from PIL import Image


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "import_a2fm_grid.py"
MASTER = APPLE2_DIR / "assets" / "game_grid_dhgr_mono_master.a2fm"
REFERENCE = APPLE2_DIR / "assets" / "game_grid_dhgr_mono_reference.png"
MASCOT = APPLE2_DIR.parent / "src" / "assets" / "main_mascot_master.png"
SPEC = importlib.util.spec_from_file_location("import_a2fm_grid", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class A2fmGridImportTests(unittest.TestCase):
    def test_master_matches_reference(self) -> None:
        main, auxiliary = IMPORTER.A2FM.split_a2fm(MASTER.read_bytes())
        decoded = IMPORTER.A2FM.decode_mono(main, auxiliary).resize(
            (IMPORTER.A2FM.SCREEN_WIDTH, IMPORTER.A2FM.SCREEN_HEIGHT * 2),
            Image.Resampling.NEAREST,
        )
        with Image.open(REFERENCE) as reference:
            self.assertEqual(
                decoded.tobytes(),
                IMPORTER.A2FM.monochrome_bytes(reference),
            )

    def test_a2fm_page_size_and_black_dynamic_cells(self) -> None:
        main, auxiliary = IMPORTER.A2FM.split_a2fm(MASTER.read_bytes())

        self.assertEqual(len(main) + len(auxiliary), IMPORTER.PAGE_BYTES * 2)
        IMPORTER.validate_black_cell_interiors(main, auxiliary)

    def test_board_geometry_fits_visible_gameplay_area(self) -> None:
        right = IMPORTER.BOARD_LEFT + 4 * IMPORTER.CELL_PITCH_X + IMPORTER.CELL_SIZE
        bottom = IMPORTER.BOARD_TOP + 4 * IMPORTER.CELL_PITCH_Y + IMPORTER.CELL_SIZE
        self.assertLessEqual(right, IMPORTER.WIDTH)
        self.assertLessEqual(bottom, IMPORTER.VISIBLE_HEIGHT)

    def test_runtime_grid_replaces_reminder_with_piece_sidebar(self) -> None:
        main, auxiliary = IMPORTER.A2FM.split_a2fm(MASTER.read_bytes())
        runtime_main, runtime_auxiliary, image = IMPORTER.build_runtime_grid(
            main,
            auxiliary,
            MASCOT,
        )

        self.assertEqual(len(runtime_main), IMPORTER.PAGE_BYTES)
        self.assertEqual(len(runtime_auxiliary), IMPORTER.PAGE_BYTES)
        self.assertEqual(IMPORTER.SIDEBAR_LABELS, ())
        self.assertIn(
            ("[N]EW GAME", 38, 176, (28, 174, 126, 181)),
            IMPORTER.PRE_RENDERED_LABELS,
        )
        self.assertIn(
            ("[I]NSTRUCTIONS", 429, 176, (424, 174, 544, 181)),
            IMPORTER.PRE_RENDERED_LABELS,
        )
        left, top, right, bottom = IMPORTER.SIDEBAR_CLEAR_BOX
        self.assertFalse(any(image.crop((left, top, right + 1, bottom + 1)).tobytes()))
        for label, label_x, label_y, clear_box in IMPORTER.PRE_RENDERED_LABELS:
            expected = Image.new("L", image.size, 0)
            IMPORTER.draw_label(expected, label, label_x, label_y, scale_x=2, scale_y=1)
            left, top, right, bottom = clear_box
            self.assertEqual(
                image.crop((left, top, right + 1, bottom + 1)).tobytes(),
                expected.crop((left, top, right + 1, bottom + 1)).tobytes(),
            )
        score_left, score_top, score_right, score_bottom = IMPORTER.SCORE_CLEAR_BOX
        self.assertFalse(any(image.crop((
            score_left,
            score_top,
            score_right + 1,
            score_bottom + 1,
        )).tobytes()))
        mascot_left, mascot_top, mascot_width, mascot_height = IMPORTER.MASCOT_BOX
        self.assertTrue(any(image.crop((
            mascot_left,
            mascot_top,
            mascot_left + mascot_width,
            mascot_top + mascot_height,
        )).tobytes()))
        self.assertFalse(any(image.crop((
            0,
            IMPORTER.FOOTER_SEPARATOR_TOP,
            IMPORTER.A2FM.SCREEN_WIDTH,
            IMPORTER.FOOTER_SEPARATOR_BOTTOM + 1,
        )).tobytes()))
        button_left, button_top, button_right, button_bottom = (
            IMPORTER.INSTRUCTIONS_BUTTON_BOX
        )
        self.assertTrue(any(image.crop((
            button_left,
            button_top,
            button_right + 1,
            button_bottom + 1,
        )).tobytes()))
        IMPORTER.validate_black_cell_interiors(runtime_main, runtime_auxiliary)

    def test_footer_buttons_use_matching_single_line_borders(self) -> None:
        image = Image.new("L", (IMPORTER.A2FM.SCREEN_WIDTH, IMPORTER.HEIGHT), 0)
        IMPORTER.draw_footer_buttons(image)
        left_box = IMPORTER.NEW_GAME_BUTTON_BOX
        right_box = IMPORTER.INSTRUCTIONS_BUTTON_BOX

        self.assertEqual(
            image.crop((left_box[0], left_box[1], left_box[2] + 1, left_box[3] + 1)).tobytes(),
            image.crop((right_box[0], right_box[1], right_box[2] + 1, right_box[3] + 1)).tobytes(),
        )
        middle_y = left_box[1] + (left_box[3] - left_box[1]) // 2
        self.assertEqual(image.getpixel((left_box[0], middle_y)), 255)
        self.assertEqual(image.getpixel((left_box[0] + 2, middle_y)), 0)


if __name__ == "__main__":
    unittest.main()
