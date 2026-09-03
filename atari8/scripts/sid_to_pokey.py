#!/usr/bin/env python3
"""Convert a C64 PSID tune into a POKEY register stream for the Atari 800.

A .sid file is not a note list -- it is 6502 machine code that writes to the
SID registers ($D400-$D41C) once per video frame.  We therefore *run* the
player in a 6502 emulator (py65), trap every SID write, reconstruct each
voice's frequency / gate / waveform / ADSR, model the SID envelope in
software, and retarget the result to POKEY ($D200-$D208).

Outputs:
  * <name>.pokey   raw stream, 6 bytes/frame: AUDF1,AUDC1,AUDF2,AUDC2,AUDF3,AUDC3
  * <name>.s       ca65 include: label, length, loop point, .byte data
  * <name>.wav     square-wave preview so the conversion can be judged by ear
  * <name>.csv     per-frame debug dump (optional, --csv)

This is a *musical* conversion, not a register-for-register one: SID's filter,
PWM, ring-mod and fine pitch have no POKEY equivalent and are not preserved.
"""
import argparse
import struct
import sys
import wave
from pathlib import Path

from py65.devices.mpu6502 import MPU
from py65.memory import ObservableMemory

# ---- C64 / Atari timing constants -----------------------------------------
C64_PAL_CLOCK = 985248.0          # SID freq register reference clock (PAL)
C64_NTSC_CLOCK = 1022730.0
FRAME_RATE = 50.0                 # PSID vsync tunes: play() called 50x/sec (PAL)
FRAME_MS = 1000.0 / FRAME_RATE

# Atari POKEY audio-divider input clocks (NTSC machine, 1.78977 MHz)
POKEY_15K = 1789773.0 / 114.0     # ~15699.8 Hz  (bass reach, coarse treble)
POKEY_64K = 1789773.0 / 28.0      # ~63920.5 Hz  (no bass)

AUDC_PURE = 0xA0                  # pure tone (clean square)
AUDC_NOISE = 0x80                 # 17-bit poly (noise / percussion)

MAX_VOL = 10                      # per-channel cap; 3 chans * 10 stays sane on POKEY

# Standard SID ADSR times in milliseconds (attack, and decay/release share table)
SID_ATTACK_MS = [2, 8, 16, 24, 38, 56, 68, 80, 100, 250, 500, 800, 1000, 3000, 5000, 8000]
SID_DECAY_MS = [6, 24, 48, 72, 114, 168, 204, 240, 300, 750, 1500, 2400, 3000, 9000, 15000, 24000]


def load_psid(path):
    data = Path(path).read_bytes()
    magic = data[0:4]
    if magic not in (b"PSID", b"RSID"):
        raise ValueError(f"not a PSID/RSID file (magic={magic!r})")
    (version, data_off, load_addr, init_addr, play_addr,
     songs, start_song, speed) = struct.unpack(">HHHHHHHI", data[4:22])
    name = data[0x16:0x36].split(b"\x00")[0].decode("latin-1")
    author = data[0x36:0x56].split(b"\x00")[0].decode("latin-1")
    released = data[0x56:0x76].split(b"\x00")[0].decode("latin-1")
    body = data[data_off:]
    if load_addr == 0:
        # real load address is the first two bytes of the data (little-endian)
        load_addr = body[0] | (body[1] << 8)
        body = body[2:]
    return {
        "version": version, "magic": magic, "load": load_addr,
        "init": init_addr, "play": play_addr, "songs": songs,
        "start": start_song, "speed": speed, "name": name,
        "author": author, "released": released, "body": body,
    }


class SidRunner:
    """Runs a PSID player and captures SID register writes per frame."""

    RET = 0x0001  # RTS trap: player returns here, we stop the CPU

    def __init__(self, sid):
        self.sid = sid
        self.mem = ObservableMemory()
        self.regs = bytearray(0x20)  # shadow of $D400-$D41F
        self.mem.subscribe_to_write(range(0xD400, 0xD420), self._on_sid_write)
        # swallow reads of unmapped I/O so nothing explodes; returns 0 anyway
        self.mpu = MPU(memory=self.mem)
        body = sid["body"]
        for i, b in enumerate(body):
            self.mem[sid["load"] + i] = b

    def _on_sid_write(self, addr, value):
        self.regs[addr - 0xD400] = value & 0xFF

    def _call(self, addr, acc=0, max_steps=5_000_000):
        m = self.mpu
        m.a = acc & 0xFF
        m.x = 0
        m.y = 0
        ret = self.RET - 1
        m.memory[0x0100 + m.sp] = (ret >> 8) & 0xFF
        m.sp = (m.sp - 1) & 0xFF
        m.memory[0x0100 + m.sp] = ret & 0xFF
        m.sp = (m.sp - 1) & 0xFF
        m.pc = addr
        steps = 0
        while m.pc != self.RET and steps < max_steps:
            m.step()
            steps += 1
        if steps >= max_steps:
            raise RuntimeError(f"player did not return from ${addr:04X} (possible busy-wait)")

    def run(self, song, frames):
        self.mpu.sp = 0xFF
        self._call(self.sid["init"], acc=song)
        out = []
        for _ in range(frames):
            self._call(self.sid["play"])
            out.append(bytes(self.regs))
        return out


def envelopes(frames_regs):
    """Software SID ADSR model -> per-voice, per-frame level 0..255."""
    n = len(frames_regs)
    levels = [[0] * 3 for _ in range(n)]
    for v in range(3):
        base = v * 7
        state = "off"   # off / attack / decay / sustain / release
        level = 0.0
        prev_gate = 0
        for f, regs in enumerate(frames_regs):
            ctrl = regs[base + 4]
            gate = ctrl & 1
            test = ctrl & 0x08
            ad = regs[base + 5]
            sr = regs[base + 6]
            atk = SID_ATTACK_MS[ad >> 4]
            dec = SID_DECAY_MS[ad & 0x0F]
            sus = (sr >> 4) / 15.0 * 255.0
            rel = SID_DECAY_MS[sr & 0x0F]

            if gate and not prev_gate:
                state = "attack"
            elif not gate and prev_gate:
                state = "release"
            prev_gate = gate

            if state == "attack":
                step = 255.0 / max(atk / FRAME_MS, 1.0)
                level += step
                if level >= 255.0:
                    level = 255.0
                    state = "decay"
            elif state == "decay":
                step = (255.0 - sus) / max(dec / FRAME_MS, 1.0)
                level -= step
                if level <= sus:
                    level = sus
                    state = "sustain"
            elif state == "sustain":
                level = sus
            elif state == "release":
                step = 255.0 / max(rel / FRAME_MS, 1.0)
                level -= step
                if level <= 0.0:
                    level = 0.0
                    state = "off"

            if test:  # oscillator held in reset -> silent
                level_out = 0.0
            else:
                level_out = level
            levels[f][v] = level_out
    return levels


def sid_freq_hz(regs, base, clock):
    freq16 = regs[base] | (regs[base + 1] << 8)
    return freq16 * clock / 16777216.0


def hz_to_audf(hz, pokey_clock):
    if hz <= 0:
        return 0
    audf = round(pokey_clock / (2.0 * hz)) - 1
    return max(0, min(255, audf))


def audf_to_hz(audf, pokey_clock):
    return pokey_clock / (2.0 * (audf + 1))


def convert(frames_regs, clock, pokey_clock, pitch_scale=1.0):
    levels = envelopes(frames_regs)
    stream = bytearray()
    debug = []
    for f, regs in enumerate(frames_regs):
        master = (regs[0x18] & 0x0F) / 15.0
        row = []
        for v in range(3):
            base = v * 7
            ctrl = regs[base + 4]
            noise = ctrl & 0x80
            hz = sid_freq_hz(regs, base, clock) * pitch_scale
            audf = hz_to_audf(hz, pokey_clock)
            vol = round(levels[f][v] / 255.0 * MAX_VOL * master)
            vol = max(0, min(MAX_VOL, vol))
            dist = AUDC_NOISE if noise else AUDC_PURE
            audc = dist | vol
            stream.append(audf)
            stream.append(audc)
            row.append((hz, audf, audf_to_hz(audf, pokey_clock), vol, bool(noise)))
        debug.append(row)
    return stream, debug


def find_loop(frames_regs, window=32, min_period=2.0):
    """Detect a loop only when a *run* of `window` consecutive frames recurs.

    Single-frame state matches are common (repeating bass/arp patterns) and
    give false positives, so we require a sustained match at least
    `min_period` seconds after the first occurrence.
    """
    n = len(frames_regs)
    keys = [bytes(r) for r in frames_regs]
    min_gap = int(min_period * FRAME_RATE)
    for start in range(0, n - window):
        block = keys[start:start + window]
        for j in range(start + min_gap, n - window):
            if keys[j:j + window] == block:
                return start, j
    return 0, n


def write_wav(path, debug, pokey_clock):
    rate = 44100
    spf = int(rate / FRAME_RATE)
    phases = [0.0, 0.0, 0.0]
    import math
    samples = bytearray()
    for row in debug:
        for _ in range(spf):
            acc = 0
            for v in range(3):
                hz, audf, real_hz, vol, noise = row[v]
                if vol <= 0:
                    continue
                if noise:
                    import random
                    s = random.uniform(-1, 1)
                else:
                    phases[v] += real_hz / rate
                    s = 1.0 if (phases[v] % 1.0) < 0.5 else -1.0
                acc += s * (vol / MAX_VOL)
            val = int(max(-1.0, min(1.0, acc / 3.0)) * 30000)
            samples += struct.pack("<h", val)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(samples))


def write_asm(path, stream, loop_frame, label, sid):
    frames = len(stream) // 6
    lines = [
        f"; Auto-generated by sid_to_pokey.py -- DO NOT EDIT BY HAND",
        f"; Source: {sid['name']} / {sid['author']} ({sid['released']})",
        f"; {frames} frames @ {int(FRAME_RATE)} Hz, 6 bytes/frame:",
        f";   AUDF1,AUDC1, AUDF2,AUDC2, AUDF3,AUDC3",
        f"",
        f".export {label}_data, {label}_end, {label}_loop",
        f".export {label}_frames",
        f"",
        f"{label}_frames = {frames}",
        f"",
        f"; Placed in its own segment so the ~5-6 KB stream can live in the free",
        f"; $A000-$BFFF RAM instead of the packed $2000-$8000 program area.",
        f".segment \"MUSIC\"",
        f"{label}_data:",
    ]
    for i in range(0, len(stream), 12):
        chunk = ", ".join(f"${b:02X}" for b in stream[i:i + 12])
        lines.append(f"    .byte {chunk}")
    lines += [
        f"{label}_end:",
        f"",
        f"; address of the loop restart frame (frame {loop_frame})",
        f"{label}_loop = {label}_data + {loop_frame * 6}",
    ]
    Path(path).write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sid", help="input .sid (PSID) file")
    ap.add_argument("-o", "--outdir", default=".", help="output directory")
    ap.add_argument("--label", default=None, help="asm symbol prefix")
    ap.add_argument("--seconds", type=float, default=20.0, help="capture duration")
    ap.add_argument("--song", type=int, default=None, help="subtune (1-based)")
    ap.add_argument("--ntsc-sid", action="store_true",
                    help="tune pitch to NTSC (~+3.8%%, matches NTSC playback)")
    ap.add_argument("--semitones", type=float, default=0.0,
                    help="transpose the whole tune by this many semitones (may be fractional)")
    ap.add_argument("--pokey-64k", action="store_true", help="use POKEY 64kHz clock")
    ap.add_argument("--detect-loop", action="store_true",
                    help="trim to a detected loop (default: loop whole capture)")
    ap.add_argument("--csv", action="store_true", help="also emit per-frame CSV")
    args = ap.parse_args()

    sid = load_psid(args.sid)
    song = (args.song if args.song is not None else sid["start"]) - 1
    clock = C64_NTSC_CLOCK if args.ntsc_sid else C64_PAL_CLOCK
    pokey_clock = POKEY_64K if args.pokey_64k else POKEY_15K
    frames = int(args.seconds * FRAME_RATE)

    print(f"Tune:     {sid['name']}")
    print(f"Author:   {sid['author']}")
    print(f"Released: {sid['released']}")
    print(f"load=${sid['load']:04X} init=${sid['init']:04X} play=${sid['play']:04X} "
          f"songs={sid['songs']} start={sid['start']}")
    print(f"Capturing song {song + 1}, {frames} frames "
          f"({args.seconds:.0f}s @ {int(FRAME_RATE)}Hz)...")

    runner = SidRunner(sid)
    frames_regs = runner.run(song, frames)

    if not args.detect_loop:
        loop_start, loop_end = 0, len(frames_regs)
    else:
        loop_start, loop_end = find_loop(frames_regs)
        if loop_end < len(frames_regs):
            print(f"Loop detected: frames {loop_start}..{loop_end} "
                  f"({(loop_end - loop_start) / FRAME_RATE:.1f}s); trimming.")
            frames_regs = frames_regs[:loop_end]

    pitch_scale = 2.0 ** (args.semitones / 12.0)
    stream, debug = convert(frames_regs, clock, pokey_clock, pitch_scale)
    if args.semitones:
        print(f"Transposed {args.semitones:+.2f} semitones "
              f"(pitch x{pitch_scale:.4f}).")

    # pitch range report
    active_hz = [c[0] for row in debug for c in row if c[3] > 0 and not c[4]]
    if active_hz:
        print(f"Active pitch range: {min(active_hz):.0f}..{max(active_hz):.0f} Hz "
              f"(POKEY {('64k' if args.pokey_64k else '15k')} clock: "
              f"{audf_to_hz(255, pokey_clock):.0f}..{audf_to_hz(0, pokey_clock):.0f} Hz)")

    name = args.label or Path(args.sid).stem.lower().replace("-", "_").replace(" ", "_")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / f"{name}.pokey").write_bytes(stream)
    write_asm(outdir / f"{name}.s", stream, loop_start, name, sid)
    write_wav(outdir / f"{name}.wav", debug, pokey_clock)
    if args.csv:
        rows = ["frame,v,hz,audf,real_hz,vol,noise"]
        for f, row in enumerate(debug):
            for v, c in enumerate(row):
                rows.append(f"{f},{v},{c[0]:.1f},{c[1]},{c[2]:.1f},{c[3]},{int(c[4])}")
        (outdir / f"{name}.csv").write_text("\n".join(rows) + "\n")

    print(f"\nWrote {len(stream)} bytes ({len(stream)//6} frames):")
    print(f"  {name}.pokey  (raw stream)")
    print(f"  {name}.s      (ca65 include)")
    print(f"  {name}.wav    (preview)")


if __name__ == "__main__":
    main()
