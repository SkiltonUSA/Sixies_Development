#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

from PIL import Image


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "import_a2fm_asset.py"
MASTER = APPLE2_DIR / "assets" / "title_dhgr_mono_master.a2fm"
REFERENCE = APPLE2_DIR / "assets" / "title_dhgr_mono_reference.png"
SPEC = importlib.util.spec_from_file_location("import_a2fm_asset", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class A2fmImportTests(unittest.TestCase):
    def test_master_splits_as_auxiliary_then_main(self) -> None:
        source = MASTER.read_bytes()
        main, auxiliary = IMPORTER.split_a2fm(source)

        self.assertEqual(len(main), IMPORTER.PAGE_BYTES)
        self.assertEqual(len(auxiliary), IMPORTER.PAGE_BYTES)
        self.assertEqual(auxiliary + main, source)

    def test_decoded_master_matches_reference(self) -> None:
        main, auxiliary = IMPORTER.split_a2fm(MASTER.read_bytes())
        decoded = IMPORTER.decode_mono(main, auxiliary).resize(
            (IMPORTER.SCREEN_WIDTH, IMPORTER.SCREEN_HEIGHT * 2),
            Image.Resampling.NEAREST,
        )
        with Image.open(REFERENCE) as reference:
            self.assertEqual(
                decoded.tobytes(),
                IMPORTER.monochrome_bytes(reference),
            )

    def test_rejects_incomplete_file(self) -> None:
        with self.assertRaises(ValueError):
            IMPORTER.split_a2fm(bytes(IMPORTER.PAGE_BYTES))


if __name__ == "__main__":
    unittest.main()
