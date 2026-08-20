#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


APPLE2_DIR = Path(__file__).parents[1]
SCRIPT = APPLE2_DIR / "scripts" / "generate_merge_effects.py"
SPEC = importlib.util.spec_from_file_location("generate_merge_effects", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class MergeEffectTests(unittest.TestCase):
    def test_reserved_face_effect_indices_are_stable(self) -> None:
        self.assertEqual(GENERATOR.EFFECT_NAMES[3], "fives")
        self.assertEqual(GENERATOR.EFFECT_NAMES[5], "sixies")

    def test_effect_geometry_is_byte_aligned_and_fits_transfer_buffer(self) -> None:
        self.assertEqual(GENERATOR.EFFECT_LEFT, 0)
        self.assertEqual(GENERATOR.EFFECT_LEFT % 14, 0)
        self.assertEqual(GENERATOR.EFFECT_WIDTH % 14, 0)
        self.assertLessEqual(GENERATOR.BANK_BYTES, 1024)
        self.assertEqual(GENERATOR.EFFECT_BYTES, 1920)
        self.assertEqual(GENERATOR.STAR_PHASE_BYTES, 88)
        self.assertEqual(GENERATOR.STAR_BYTES, 616)
        self.assertLessEqual(GENERATOR.STAR_BYTES, 1024)

    def test_c64_star_is_packed_for_every_signal_phase(self) -> None:
        mask = GENERATOR.build_star_mask()
        blits = GENERATOR.build_star_blits()

        self.assertEqual(len(mask), 48 * 24)
        self.assertEqual(sum(mask), 112)
        self.assertEqual(len(blits), GENERATOR.STAR_BYTES)
        for phase in range(GENERATOR.STAR_PHASES):
            offset = phase * GENERATOR.STAR_PHASE_BYTES
            variant = blits[offset : offset + GENERATOR.STAR_PHASE_BYTES]
            self.assertTrue(any(variant))
            for y in range(GENERATOR.STAR_ACTIVE_HEIGHT):
                for signal in range(GENERATOR.STAR_SIGNAL_WIDTH):
                    shifted = phase + signal
                    packed = variant[
                        y * GENERATOR.STAR_SEQUENCE_BYTES + shifted // 7
                    ]
                    actual = bool(packed & (1 << (shifted % 7)))
                    source_y = y + GENERATOR.STAR_ACTIVE_TOP
                    expected = bool(mask[source_y * GENERATOR.STAR_SIGNAL_WIDTH + signal])
                    self.assertEqual(actual, expected)

    def test_all_masters_pack_into_both_banks(self) -> None:
        checksums = []
        for name in GENERATOR.EFFECT_NAMES:
            source = APPLE2_DIR / "assets" / f"merge_{name}_master.png"
            mask = GENERATOR.render_mask(source)
            auxiliary, main = GENERATOR.pack_banks(mask)
            self.assertEqual(len(auxiliary), GENERATOR.BANK_BYTES)
            self.assertEqual(len(main), GENERATOR.BANK_BYTES)
            self.assertTrue(any(auxiliary))
            self.assertTrue(any(main))
            checksums.append((sum(auxiliary) + sum(main)) & 0xFFFF)
        self.assertEqual(
            checksums,
            [37373, 60140, 6094, 948, 21934, 169, 10679, 5510, 51099, 52272],
        )

    def test_scanline_addresses_cover_effect_height(self) -> None:
        self.assertEqual(GENERATOR.EFFECT_TOP, 56)
        addresses = [
            GENERATOR.hgr_address(GENERATOR.EFFECT_TOP + row)
            for row in range(GENERATOR.EFFECT_HEIGHT)
        ]
        self.assertEqual(len(addresses), GENERATOR.EFFECT_HEIGHT)
        self.assertEqual(len(set(addresses)), GENERATOR.EFFECT_HEIGHT)
        self.assertTrue(all(0x2000 <= address < 0x4000 for address in addresses))


if __name__ == "__main__":
    unittest.main()
