import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("generate_assets", ROOT / "scripts/generate-assets.py")
ASSETS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ASSETS)


class CalloutBoxTests(unittest.TestCase):
    def test_callouts_use_clear_comic_art_with_transparent_backgrounds(self):
        for name in ASSETS.CALLOUTS:
            template = ASSETS.CALLOUT_TEMPLATES[name]
            callout = ASSETS.make_callout(ROOT / "assets/callouts" / "comic" / f"{template}.png")
            self.assertEqual(callout.size, (64, 32))
            self.assertGreater(sum(pixel == 0 for pixel in callout.getdata()), 256)
            self.assertGreater(sum(pixel == 1 for pixel in callout.getdata()), 64)
            self.assertGreater(sum(pixel == 3 for pixel in callout.getdata()), 64)
            self.assertGreater(sum(pixel == 3 for pixel in callout.getdata()), 8)


if __name__ == "__main__":
    unittest.main()
