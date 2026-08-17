#!/usr/bin/env python3
"""Tests for the reusable PNG to NES graphics converter."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from nes_graphics import (  # noqa: E402
    RgbaImage,
    build_tiles,
    choose_palette,
    decode_tile,
    encode_tile,
    expand_metatile_atlas,
    map_nametable_to_chr,
    parse_ines,
    read_png,
    render_tilemap,
    write_png,
)


class NesGraphicsTests(unittest.TestCase):
    def test_png_round_trip_preserves_rgba_pixels(self):
        image = RgbaImage(2, 2, (
            ((255, 0, 0, 255), (0, 255, 0, 128)),
            ((0, 0, 255, 0), (10, 20, 30, 255)),
        ))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "round-trip.png"
            write_png(path, image)
            self.assertEqual(read_png(path), image)

    def test_chr_bitplanes_encode_four_pixel_values(self):
        rows = tuple(tuple(value for _ in range(8)) for value in range(4))
        tile = encode_tile(rows + rows)
        self.assertEqual(tile[:8], bytes((0x00, 0xff, 0x00, 0xff) * 2))
        self.assertEqual(tile[8:], bytes((0x00, 0x00, 0xff, 0xff) * 2))
        self.assertEqual(decode_tile(tile), rows + rows)

    def test_tile_builder_deduplicates_repeated_tiles(self):
        tile = tuple(tuple((x + y) & 3 for x in range(8)) for y in range(8))
        indexed = tuple(left + left for left in tile)
        result = build_tiles(indexed)
        self.assertEqual(result.tile_count, 1)
        self.assertEqual(result.nametable, b"\x00\x00")
        self.assertEqual(len(result.chr_data), 16)

    def test_automatic_palette_has_four_nes_entries(self):
        image = RgbaImage(2, 2, (
            ((255, 0, 0, 255), (0, 255, 0, 255)),
            ((0, 0, 255, 255), (0, 0, 0, 0)),
        ))
        palette = choose_palette(image)
        self.assertEqual(len(palette), 4)
        self.assertEqual(palette[0], 0x0f)
        self.assertTrue(all(0 <= value < 64 for value in palette))

    def test_nametable_mapping_and_rendering(self):
        first = tuple((0,) * 8 for _ in range(8))
        second = tuple((3,) * 8 for _ in range(8))
        chr_data = encode_tile(first) + encode_tile(second)
        self.assertEqual(
            map_nametable_to_chr(chr_data, b"\x01\x00"),
            encode_tile(second) + encode_tile(first),
        )
        rendered = render_tilemap(chr_data, b"\x01\x00", 2, 1)
        self.assertEqual(rendered[0], (3,) * 8 + (0,) * 8)

    def test_metatile_expansion_supports_packed_rows(self):
        definitions = bytes((1, 2, 3, 4, 5, 6, 7, 8))
        self.assertEqual(
            expand_metatile_atlas(definitions, 2, 2, columns=2),
            bytes((1, 2, 5, 6, 3, 4, 7, 8)),
        )

    def test_ines_parser_extracts_chr_rom(self):
        header = b"NES\x1a" + bytes((1, 1, 0, 0)) + bytes(8)
        rom = header + bytes(16384) + bytes((0x5a,)) * 8192
        parsed = parse_ines(rom)
        self.assertEqual(len(parsed.prg_rom), 16384)
        self.assertEqual(parsed.chr_rom, bytes((0x5a,)) * 8192)

    def test_cli_writes_complete_asset_bundle(self):
        image = RgbaImage(8, 8, tuple(
            tuple((240, 80, 32, 255) if x == y else (0, 0, 0, 0)
                  for x in range(8))
            for y in range(8)
        ))
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory / "source.png"
            prefix = directory / "converted"
            write_png(source, image)
            subprocess.run((
                sys.executable,
                str(ROOT / "scripts/convert-png-to-nes.py"),
                str(source),
                str(prefix),
                "--palette", "0f,00,16,27",
            ), check=True, capture_output=True, text=True)
            self.assertEqual((directory / "converted.chr").stat().st_size, 4096)
            self.assertEqual((directory / "converted.nam").read_bytes(), b"\x00")
            self.assertEqual((directory / "converted.pal").read_bytes(),
                             bytes((0x0f, 0x00, 0x16, 0x27)))
            self.assertTrue((directory / "converted.json").is_file())
            self.assertEqual(read_png(directory / "converted.preview.png").width, 8)

    def test_chr_render_cli_accepts_ines_rom(self):
        header = b"NES\x1a" + bytes((1, 1, 0, 0)) + bytes(8)
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            rom = directory / "game.nes"
            preview = directory / "chr.png"
            rom.write_bytes(header + bytes(16384) + bytes(8192))
            subprocess.run((
                sys.executable,
                str(ROOT / "scripts/render-nes-chr.py"),
                str(rom),
                str(preview),
                "--ines", "--max-tiles", "1",
            ), check=True, capture_output=True, text=True)
            image = read_png(preview)
            self.assertEqual((image.width, image.height), (128, 8))


if __name__ == "__main__":
    unittest.main()
