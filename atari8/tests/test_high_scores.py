from pathlib import Path
import tempfile
import unittest

import sys


ATARI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ATARI / "scripts"))
import preserve_high_scores  # noqa: E402


class HighScorePersistenceTests(unittest.TestCase):
    def test_seed_table_is_valid_sorted_and_matches_reference_scores(self):
        table = preserve_high_scores.default_table()
        self.assertEqual(len(table), 56)
        self.assertTrue(preserve_high_scores.valid_table(table))
        scores = []
        for index in range(10):
            offset = 6 + index * 5
            scores.append(table[offset + 3] | table[offset + 4] << 8)
        self.assertEqual(scores, [1349, 1020, 893, 802, 755, 650, 540, 430, 320, 210])

    def test_existing_valid_sector_survives_disk_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / "old.atr"
            new = root / "new.atr"
            output = root / "output.atr"
            image_size = preserve_high_scores.ATR_HEADER_BYTES + 720 * 128

            table = bytearray(preserve_high_scores.default_table())
            table[6:9] = b"ZED"
            table[9:11] = (2000).to_bytes(2, "little")
            table[5] = sum(table[6:]) & 0xFF
            old_image = bytearray(image_size)
            offset = preserve_high_scores.sector_offset()
            old_image[offset : offset + len(table)] = table
            old.write_bytes(old_image)
            new.write_bytes(bytes(image_size))

            saved = preserve_high_scores.read_table(old)
            self.assertEqual(saved, bytes(table))
            preserve_high_scores.install_table(new, output, saved)
            self.assertEqual(preserve_high_scores.read_table(output), bytes(table))

    def test_built_disk_contains_a_valid_table(self):
        table = preserve_high_scores.read_table(ATARI / "build" / "sixies.atr")
        self.assertIsNotNone(table)


if __name__ == "__main__":
    unittest.main()
