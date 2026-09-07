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
    def test_compiled_generator_has_requested_opening_distribution(self) -> None:
        symbols = labels()
        memory = [0] * 0x10000
        load_xex(memory)
        mpu = MPU(memory=memory)
        state = symbols["rng_state"]
        memory[state : state + 4] = [1, 0, 1, 0]

        # Use the same initial advance as new_game, then execute the real linked
        # spawn routine so branches and multiple random draws are covered.
        call(mpu, symbols["random16"])
        singles: Counter[int] = Counter()
        pairs: Counter[tuple[int, int]] = Counter()
        for _ in range(12000):
            call(mpu, symbols["spawn_piece"])
            if memory[symbols["piece_count"]] == 2:
                pairs[(memory[symbols["piece_a"]], memory[symbols["piece_b"]])] += 1
            else:
                singles[memory[symbols["piece_a"]]] += 1

        self.assertGreater(sum(pairs.values()), 8700)
        self.assertLess(sum(pairs.values()), 9300)
        self.assertEqual(set(singles), {1, 2, 3})
        self.assertEqual(set(pairs), {(1,2), (1,3), (2,3), (3,1), (3,2), (3,3)})
        self.assertGreater(pairs[(3,3)], 480)
        self.assertLess(pairs[(3,3)], 720)
        for count in singles.values():
            self.assertGreater(count, 850)
            self.assertLess(count, 1150)
        for pair, count in pairs.items():
            if pair != (3,3):
                self.assertGreater(count, 1450)
                self.assertLess(count, 1900)


if __name__ == "__main__":
    unittest.main()
