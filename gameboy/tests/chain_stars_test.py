import importlib.util
from pathlib import Path
import re
import sys
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("generate_assets", ROOT / "scripts/generate-assets.py")
ASSETS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ASSETS)


class ChainStarTests(unittest.TestCase):
    def test_transparent_native_tiles_match_rom_art(self):
        stars = ASSETS.make_chain_stars(ROOT / "assets/chain_stars_master.png")
        self.assertEqual(len(stars), 2)
        for star in stars:
            self.assertEqual(star.size, (16, 16))
            self.assertEqual(set(star.getdata()), {0, 1, 2, 3})
            for corner in ((0, 0), (15, 0), (0, 15), (15, 15)):
                self.assertEqual(star.getpixel(corner), 0)
        source = (ROOT / "src/generated_callouts.c").read_text()
        data = source.split("const uint8_t chain_star_tiles[] = {", 1)[1].split("};", 1)[0]
        actual = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", data))
        tiles = ASSETS.split_tiles(stars[0])
        expected = bytes(ASSETS.pack_tiles((tiles[0], tiles[2], tiles[1], tiles[3])))
        self.assertEqual(len(actual), 64)
        self.assertEqual(actual, expected)
        dmg_data = source.split("const uint8_t chain_star_dmg_tiles[] = {", 1)[1].split("};", 1)[0]
        dmg_actual = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", dmg_data))
        self.assertEqual(dmg_actual, expected)
        self.assertNotEqual(ASSETS.CHAIN_STAR_PALETTES[0][2], ASSETS.CHAIN_STAR_PALETTES[1][2])

    def test_chain_badge_tiles_are_paired_for_8x16_sprites(self):
        badge = ASSETS.make_chain_reaction_sprite(ROOT / "assets/chain_reaction.png")
        self.assertEqual(badge.size, (64, 32))
        self.assertGreater(sum(pixel == 0 for pixel in badge.getdata()), 256)
        self.assertGreater(sum(pixel == 3 for pixel in badge.getdata()), 64)
        source = (ROOT / "src/generated_callouts.c").read_text()
        data = source.split("const uint8_t chain_reaction_tiles[] = {", 1)[1].split("};", 1)[0]
        tiles = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", data))
        rendered = Image.new("L", badge.size)

        for row in range(2):
            for column in range(8):
                for half in range(2):
                    tile = Image.new("L", (8, 8))
                    pixels = []
                    offset = ((row * 8 + column) * 2 + half) * 16
                    for pixel_y in range(8):
                        low = tiles[offset + pixel_y * 2]
                        high = tiles[offset + pixel_y * 2 + 1]
                        pixels.extend((low >> (7 - pixel_x) & 1) | ((high >> (7 - pixel_x) & 1) << 1) for pixel_x in range(8))
                    tile.putdata(pixels)
                    rendered.paste(tile, (column * 8, row * 16 + half * 8))
        self.assertEqual(rendered.tobytes(), badge.tobytes())

    def test_chain_badge_has_no_cgb_only_renderer(self):
        source = (ROOT / "src/generated_callouts.c").read_text()
        self.assertNotIn("chain_reaction_native_tiles", source)


if __name__ == "__main__":
    unittest.main()
