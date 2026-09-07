"""Execute linked game routines; fake OS ticks/SIO, not game instructions.

This is CPU-level regression coverage, not an ANTIC/POKEY emulator. Rendering
tests inspect framebuffer bytes; hardware timing still needs Atari800/hardware.
"""
from py65.devices.mpu6502 import MPU
from test_rng_probabilities import labels, load_xex, RETURN_PC


class Machine:
    def __init__(self):
        self.symbols = labels()
        self.memory = [0] * 65536
        load_xex(self.memory)
        self.cpu = MPU(memory=self.memory)
        self.memory[0x2FC] = 255  # CH
        self.memory[0xD01F] = 7  # console buttons released
        self.memory[0xD20F] = 4  # no physical key
        self.memory[0xD40B] = 0x7C  # vertical blank for video setup
        for port in range(2):
            self.memory[0x278 + port] = 15
            self.memory[0x284 + port] = 1

    def get(self, name):
        return self.memory[self.symbols[name]]

    def set(self, name, value):
        self.memory[self.symbols[name]] = value

    def region(self, name, size):
        start = self.symbols[name]
        return self.memory[start:start + size]

    def put(self, name, values):
        start = self.symbols[name]
        self.memory[start:start + len(values)] = values

    def stub(self, *names):
        for name in names:
            self.memory[self.symbols[name]] = 0x60  # RTS at presentation boundary

    def call(self, name, a=0, x=0, y=0, ticks=False, hook=None, limit=1000000):
        cpu = self.cpu
        cpu.pc, cpu.a, cpu.x, cpu.y, cpu.sp = self.symbols[name], a, x, y, 255
        cpu.stPushWord(RETURN_PC - 1)
        for step in range(limit):
            if ticks and step % 100 == 99:
                self.memory[0x14] = (self.memory[0x14] + 1) & 255
            if hook:
                hook(self)
            cpu.step()
            if cpu.pc == RETURN_PC:
                return cpu.a
        raise AssertionError(f"{name} did not return; PC=${cpu.pc:04X}")
