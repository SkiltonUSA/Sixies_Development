from pathlib import Path
import sys
import unittest

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dice_shading import FACE_SHADES, SHADE_PERMUTATIONS, shade_die


class DiceShadingTests(unittest.TestCase):
    def test_all_24_permutations_preserve_transparency_and_pixels(self):
        source = Image.new("RGBA", (18, 18), (255, 255, 255, 255))
        source.putpixel((0, 0), (255, 255, 255, 0))
        indexed = Image.new("L", source.size)
        indexed.putdata([index % 4 for index in range(324)])
        original = indexed.tobytes(), source.tobytes()
        results = set()
        for mapping in SHADE_PERMUTATIONS:
            self.assertEqual(sorted(mapping), [0, 1, 2, 3])
            result = shade_die(indexed, source, mapping)
            self.assertEqual(result.size, (18, 18))
            self.assertEqual(result.getpixel((0, 0)), 0)
            self.assertEqual(list(result.getdata())[1:], [mapping[index % 4] for index in range(1, 324)])
            results.add(result.tobytes())
        self.assertEqual(len(results), 24)
        self.assertEqual((indexed.tobytes(), source.tobytes()), original)

    def test_selected_faces_have_distinct_high_contrast_shading(self):
        self.assertEqual(len(set(FACE_SHADES)), 6)
        for mapping in FACE_SHADES:
            self.assertIn(mapping, SHADE_PERMUTATIONS)
            self.assertGreaterEqual(abs(mapping[1] - mapping[3]), 2)


if __name__ == "__main__":
    unittest.main()
