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
    decode_attribute_table,
    decode_tile,
    encode_attribute_table,
    encode_tile,
    expand_metatile_atlas,
    map_nametable_to_chr,
    nesst_rle_decode,
    nesst_rle_encode,
    parse_ines,
    parse_nesst_nam,
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

    def test_nes_attributes_round_trip_four_quadrants(self):
        palette_grid = (
            (0, 0, 1, 1),
            (0, 0, 1, 1),
            (2, 2, 3, 3),
            (2, 2, 3, 3),
        )
        attributes = encode_attribute_table(palette_grid)
        self.assertEqual(attributes, b"\xe4")
        self.assertEqual(decode_attribute_table(attributes, 4, 4), palette_grid)

    def test_nesst_rle_matches_reference_format(self):
        source = b"\x01\x01\x01\x01\x02"
        packed = nesst_rle_encode(source)
        self.assertEqual(packed, b"\x00\x01\x00\x03\x02\x00\x00")
        self.assertEqual(nesst_rle_decode(packed, expected_size=5), source)
        self.assertEqual(
            nesst_rle_encode(b"\x01\x01\x01\x02"),
            b"\x00\x01\x00\x02\x02\x00\x00",
        )

    def test_nesst_nam_accepts_tiles_with_or_without_attributes(self):
        tiles = bytes(960)
        self.assertEqual(parse_nesst_nam(tiles).attributes, bytes(64))
        attributes = bytes((0xe4,)) + bytes(63)
        self.assertEqual(parse_nesst_nam(tiles + attributes).attributes, attributes)

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

    def test_chr_render_cli_accepts_nesst_screen(self):
        solid = encode_tile(tuple((1,) * 8 for _ in range(8)))
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            chr_path = directory / "screen.chr"
            nam_path = directory / "screen.rle"
            pal_path = directory / "screen.pal"
            preview = directory / "screen.png"
            chr_path.write_bytes(solid)
            nam_path.write_bytes(nesst_rle_encode(bytes(1024)))
            pal_path.write_bytes(bytes((0x0f, 0x16, 0x27, 0x30)) * 4)
            subprocess.run((
                sys.executable,
                str(ROOT / "scripts/render-nes-chr.py"),
                str(chr_path),
                str(preview),
                "--nesst-nam", str(nam_path),
                "--nesst-palette", str(pal_path),
            ), check=True, capture_output=True, text=True)
            image = read_png(preview)
            self.assertEqual((image.width, image.height), (256, 240))


if __name__ == "__main__":
    unittest.main()
