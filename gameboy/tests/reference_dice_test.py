import importlib.util
from pathlib import Path
import sys
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("atari_dice", ROOT / "scripts/rebuild-atari-dice.py")
ATARI_DICE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ATARI_DICE)


class AtariDiceTests(unittest.TestCase):
    def test_all_faces_are_rebuilt_exactly_from_the_atari_sprites(self):
        for face, name in enumerate(ATARI_DICE.FACE_NAMES):
            with Image.open(ROOT / "assets/dice" / f"{name}_18x18.png") as source:
                actual = source.convert("RGBA")
            self.assertEqual(actual.size, (18, 18))
            self.assertEqual(actual.tobytes(), ATARI_DICE.source_die(face).tobytes())

    def test_atari_faces_keep_one_pixel_canvas_inset_and_visible_pips(self):
        for face in range(6):
            die = ATARI_DICE.reference_die(face)
            self.assertTrue(all(die.getpixel((column, row)) == 0
                                for row in range(18) for column in range(18)
                                if column in (0, 17) or row in (0, 17)))
            self.assertGreater(sum(die.getpixel((column, row)) == ATARI_DICE.FACE_STYLES[face][2]
                                   for row in range(18) for column in range(18)), 0)

    def test_each_face_uses_a_unique_body_outline_and_pip_treatment(self):
        self.assertEqual(len(set(ATARI_DICE.FACE_STYLES)), 6)
        for style in ATARI_DICE.FACE_STYLES:
            self.assertEqual(sorted(style), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
