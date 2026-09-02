from pathlib import Path
import tempfile
import unittest

from PIL import Image

import sys

ATARI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ATARI / "scripts"))
import generate_assets  # noqa: E402


class AssetPipelineTests(unittest.TestCase):
    def test_a2fm_title_matches_reference_and_atari_geometry(self):
        decoded = generate_assets.decode_a2fm_title()
        self.assertEqual(decoded.size, (560, 192))
        self.assertIsNotNone(decoded.getbbox())
        self.assertEqual(generate_assets.make_atari_title().size, (320, 110))

    def test_apple_presentation_art_converts_to_atari_panels(self):
        for name in ("presents_master.ppm", "game_over_master.png"):
            panel = generate_assets.make_atari_presentation(generate_assets.APPLE / name)
            self.assertEqual(panel.size, (240, 120), name)
            self.assertIsNotNone(panel.getbbox(), name)

    def test_instructions_rebuild_supplied_design_for_atari_controls(self):
        screen = generate_assets.make_atari_instructions()
        self.assertEqual(screen.size, (320, 192))
        self.assertIsNotNone(screen.getbbox())

    def test_acme_dice_have_expected_geometry_and_padding(self):
        names = ("one", "two", "three", "four", "five", "six")
        for name in names:
            die = generate_assets.load_acme_die(ATARI / "assets" / "dice" / f"die_{name}.asm")
            self.assertEqual(die.size, (32, 24))
            self.assertEqual(die.crop((0, 0, 32, 2)).getbbox(), None)
            self.assertEqual(die.crop((0, 22, 32, 24)).getbbox(), None)

    def test_merge_star_matches_shared_sprite_and_fits_one_cell(self):
        star = generate_assets.load_merge_star()
        self.assertEqual(star.size, (32, 24))
        self.assertIsNotNone(star.getbbox())
        self.assertEqual(star.crop((0, 0, 4, 24)).getbbox(), None)
        self.assertEqual(star.crop((28, 0, 32, 24)).getbbox(), None)

    def test_packed_exclamations_decode_to_six_atari_banners(self):
        images = generate_assets.load_exclamation_images()
        self.assertEqual(set(images), {"yay", "wow", "boom", "fives", "sixies", "awesome"})
        for name, banner in images.items():
            self.assertEqual(banner.size, (80, 24), name)
            self.assertIsNotNone(banner.getbbox(), name)

    def test_official_exclamation_words_fill_all_named_atlas_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_assets.build(root / "assets", root / "previews")
            packed = (root / "assets" / "callouts.bin").read_bytes()
            names = (
                "awesome", "boom", "dang", "fives", "lets_go",
                "sixies", "whoa", "wow", "yeah", "yes",
            )
            for slot, name in enumerate(names):
                with Image.open(generate_assets.APPLE / f"merge_{name}_master.png") as source:
                    image = generate_assets.contain(source, (80, 24), 170)
                expected = generate_assets.pack_1bpp(image)
                self.assertEqual(packed[slot * 240 : (slot + 1) * 240], expected, name)

    def test_generated_binary_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_assets.build(root / "assets", root / "previews")
            expected = {
                "mascot.bin": 10 * 100,
                "dice.bin": 6 * 4 * 24,
                "invalid.bin": 4 * 24,
                "merge_star.bin": 4 * 24,
                "callouts.bin": 10 * 10 * 24,
                "font.bin": 2048,
            }
            for name, length in expected.items():
                self.assertEqual((root / "assets" / name).stat().st_size, length, name)

            for name in (
                "title_logo.rle",
                "presents.rle",
                "instructions.rle",
                "game_over.rle",
            ):
                packed = (root / "assets" / name).read_bytes()
                self.assertLess(len(packed), 7936, name)
                self.assertEqual(len(generate_assets.unpack_rle(packed)), 7936, name)

    def test_c64_mascot_uses_bitmap_and_screen_metadata(self):
        mascot = generate_assets.load_c64_mascot()
        self.assertEqual(mascot.size, (64, 80))
        self.assertIsNotNone(mascot.getbbox())
        self.assertEqual(len(generate_assets.pack_1bpp(mascot)), 640)

    def test_detailed_mascot_retains_face_and_fills_sidebar(self):
        mascot = generate_assets.load_detailed_mascot()
        self.assertEqual(mascot.size, (80, 100))
        self.assertIsNotNone(mascot.getbbox())
        # Both eyes, the mouth, and the outer head contour leave foreground
        # transitions across the central face scanlines.
        for y in (20, 30, 40):
            row = [mascot.getpixel((x, y)) for x in range(mascot.width)]
            transitions = sum(left != right for left, right in zip(row, row[1:]))
            self.assertGreaterEqual(transitions, 6, y)

    def test_preview_atlas_is_inspectable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_assets.build(root / "assets", root / "previews")
            with Image.open(root / "previews" / "dice.png") as dice:
                self.assertEqual(dice.size, (192, 24))
            with Image.open(root / "previews" / "callouts.png") as callouts:
                self.assertEqual(callouts.size, (80, 240))


if __name__ == "__main__":
    unittest.main()
