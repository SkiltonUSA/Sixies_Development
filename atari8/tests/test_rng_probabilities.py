#!/usr/bin/env python3

from collections import Counter
from pathlib import Path
import re
import unittest

from py65.devices.mpu6502 import MPU


ATARI = Path(__file__).resolve().parents[1]
RETURN_PC = 0x0400


def labels() -> dict[str, int]:
    result: dict[str, int] = {}
    for line in (ATARI / "build" / "sixies.lbl").read_text().splitlines():
        match = re.fullmatch(r"al ([0-9A-Fa-f]{6}) \.([A-Za-z0-9_]+)", line)
        if match:
            result[match.group(2)] = int(match.group(1), 16)
    return result


def load_xex(memory: list[int]) -> None:
    data = (ATARI / "build" / "sixies.xex").read_bytes()
    offset = 0
    while offset + 1 < len(data):
        start = int.from_bytes(data[offset : offset + 2], "little")
        offset += 2
        if start == 0xFFFF:
            continue
        end = int.from_bytes(data[offset : offset + 2], "little")
        offset += 2
        size = end - start + 1
        memory[start : end + 1] = data[offset : offset + size]
        offset += size


def call(mpu: MPU, address: int, x: int = 0) -> int:
    mpu.pc = address
    mpu.x = x
    mpu.sp = 0xFF
    mpu.stPushWord(RETURN_PC - 1)
    for _ in range(2000):
        mpu.step()
        if mpu.pc == RETURN_PC:
            return mpu.a
    raise AssertionError("6502 probability routine did not return")


class RuntimeProbabilityTests(unittest.TestCase):
    def test_compiled_rng_reaches_every_apple_piece_at_expected_frequency(self) -> None:
        symbols = labels()
        memory = [0] * 0x10000
        load_xex(memory)
        mpu = MPU(memory=memory)
        state = symbols["rng_state"]
        memory[state : state + 4] = [1, 0, 1, 0]

        # srand() on Apple IIe advances once while installing its seed.
        call(mpu, symbols["random16"])
        singles: Counter[int] = Counter()
        pairs: Counter[int] = Counter()
        pair_count = 0
        single_count = 0
        for _ in range(9000):
            if call(mpu, symbols["random_mod_x"], 3) == 0:
                single_count += 1
                singles[call(mpu, symbols["random_mod_x"], 3)] += 1
            else:
                pair_count += 1
                pairs[call(mpu, symbols["random_mod_x"], 6)] += 1

        self.assertGreater(pair_count, 5800)
        self.assertLess(pair_count, 6200)
        self.assertEqual(set(singles), {0, 1, 2})
        self.assertEqual(set(pairs), {0, 1, 2, 3, 4, 5})
        for count in (*singles.values(), *pairs.values()):
            self.assertGreater(count, 850)
            self.assertLess(count, 1150)


if __name__ == "__main__":
    unittest.main()
