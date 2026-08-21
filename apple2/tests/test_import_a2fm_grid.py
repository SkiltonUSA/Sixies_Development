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
        self.assertEqual(IMPORTER.SIDEBAR_LABELS, (("CUR", 459, 15),))
        for text, x, y in IMPORTER.SIDEBAR_LABELS:
            self.assertTrue(any(image.crop((458, y, 545, y + 10)).tobytes()))
        for top in IMPORTER.DIE_TOPS[:4]:
            self.assertFalse(any(image.crop((494, top, 542, top + 24)).tobytes()))
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
        IMPORTER.validate_black_cell_interiors(runtime_main, runtime_auxiliary)


if __name__ == "__main__":
    unittest.main()
