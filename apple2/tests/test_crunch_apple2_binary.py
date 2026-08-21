#!/usr/bin/env python3

import importlib.util
from pathlib import Path
import struct
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "crunch_apple2_binary.py"
SPEC = importlib.util.spec_from_file_location("crunch_apple2_binary", SCRIPT)
CRUNCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CRUNCH)


def applesingle(data_fork: bytes, file_type: int, aux_type: int) -> bytes:
    header = struct.pack(
        ">II16sH",
        CRUNCH.APPLESINGLE_MAGIC,
        CRUNCH.APPLESINGLE_VERSION,
        bytes(16),
        2,
    )
    prodos_info = struct.pack(">HHI", 0x00C3, file_type, aux_type)
    entries = (
        struct.pack(">III", CRUNCH.DATA_FORK_ID, 58, len(data_fork))
        + struct.pack(">III", CRUNCH.PRODOS_INFO_ID, 50, len(prodos_info))
    )
    return header + entries + prodos_info + data_fork


class CrunchApple2BinaryTests(unittest.TestCase):
    def test_parses_cc65_applesingle_metadata(self) -> None:
        payload = b"native-6502-code"
        parsed = CRUNCH.parse_applesingle(applesingle(payload, 0x06, 0x4000))
        self.assertEqual(parsed, (payload, 0x06, 0x4000))

    def test_rejects_truncated_entry(self) -> None:
        image = applesingle(b"code", 0x06, 0x4000)[:-1]
        with self.assertRaisesRegex(ValueError, "extends past end"):
            CRUNCH.parse_applesingle(image)

    def test_sfx_stub_calls_machine_entry_at_080d(self) -> None:
        self.assertEqual(CRUNCH.SFX_BASIC_ADDRESS, 0x0801)
        self.assertEqual(CRUNCH.SFX_LOAD_ADDRESS, 0x080D)
        self.assertEqual(len(CRUNCH.SFX_BASIC_STUB), 12)
        self.assertIn(b"2061", CRUNCH.SFX_BASIC_STUB)


if __name__ == "__main__":
    unittest.main()
