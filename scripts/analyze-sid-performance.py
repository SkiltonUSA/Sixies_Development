#!/usr/bin/env python3
"""Trace a PSID play routine and summarize its frame-level SID performance."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path


PAL_CLOCK = 985248.0
SID_BASE = 0xD400
SID_SIZE = 25
RETURN_PC = 0x02FF
VOICE_OFFSETS = (0, 7, 14)
WAVE_NAMES = {
    0x10: "triangle",
    0x20: "saw",
    0x30: "triangle+saw",
    0x40: "pulse",
    0x50: "triangle+pulse",
    0x60: "saw+pulse",
    0x70: "triangle+saw+pulse",
    0x80: "noise",
}


class TraceMemory:
    def __init__(self) -> None:
        self.data = bytearray(65536)
        self.frame = -1
        self.sid_writes: list[list[tuple[int, int]]] = []

    def __getitem__(self, address: int) -> int:
        return self.data[address & 0xFFFF]

    def __setitem__(self, address: int, value: int) -> None:
        address &= 0xFFFF
        value &= 0xFF
        self.data[address] = value
        if self.frame >= 0 and SID_BASE <= address < SID_BASE + SID_SIZE:
            self.sid_writes[self.frame].append((address - SID_BASE, value))

    def begin_frame(self, frame: int) -> None:
        self.frame = frame
        self.sid_writes.append([])


def be16(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def parse_psid(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] not in (b"PSID", b"RSID"):
        raise ValueError(f"{path} is not a PSID/RSID file")
    data_offset = be16(data, 6)
    load = be16(data, 8)
    payload = data[data_offset:]
    if load == 0:
        load = payload[0] | (payload[1] << 8)
        payload = payload[2:]
    return {
        "path": str(path),
        "title": data[0x16:0x36].split(b"\0", 1)[0].decode("latin-1"),
        "author": data[0x36:0x56].split(b"\0", 1)[0].decode("latin-1"),
        "released": data[0x56:0x76].split(b"\0", 1)[0].decode("latin-1"),
        "load": load,
        "init": be16(data, 10) or load,
        "play": be16(data, 12),
        "songs": be16(data, 14),
        "start_song": be16(data, 16),
        "speed": int.from_bytes(data[18:22], "big"),
        "payload": payload,
    }


def call_routine(mpu, address: int, a: int = 0, max_steps: int = 200000) -> int:
    mpu.pc = address
    mpu.a = a
    mpu.x = 0
    mpu.y = 0
    mpu.sp = 0xFF
    mpu.stPushWord((RETURN_PC - 1) & 0xFFFF)
    for step in range(max_steps):
        mpu.step()
        if mpu.pc == RETURN_PC:
            return step + 1
    raise RuntimeError(f"routine ${address:04x} did not return after {max_steps} steps")


def sid_frequency(register: int) -> float:
    return register * PAL_CLOCK / 16777216.0


def midi_note(register: int) -> float | None:
    frequency = sid_frequency(register)
    if frequency <= 0:
        return None
    return 69.0 + 12.0 * math.log2(frequency / 440.0)


def nearest_note(register: int) -> int | None:
    note = midi_note(register)
    return round(note) if note is not None else None


def waveform_name(control: int) -> str:
    return WAVE_NAMES.get(control & 0xF0, f"${control & 0xF0:02x}")


def state_digest(memory: TraceMemory, load: int, payload_size: int) -> bytes:
    state = (
        memory.data[:0x100]
        + memory.data[load : load + payload_size]
        + memory.data[SID_BASE : SID_BASE + SID_SIZE]
    )
    return hashlib.blake2b(state, digest_size=12).digest()


def trace_psid(meta: dict, frames: int) -> dict:
    try:
        from py65.devices.mpu6502 import MPU
    except ImportError as exc:
        raise RuntimeError("py65 is required; add .tools/py65 to PYTHONPATH") from exc

    memory = TraceMemory()
    load = meta["load"]
    payload = meta["payload"]
    memory.data[load : load + len(payload)] = payload
    memory.data[0x02A6] = 1  # PAL flag used by some players.
    mpu = MPU(memory=memory)
    init_steps = call_routine(mpu, meta["init"], meta["start_song"] - 1)

    snapshots: list[bytes] = []
    loop_start = None
    loop_frames = None
    seen: dict[bytes, int] = {}
    play_steps: list[int] = []
    for frame in range(frames):
        memory.begin_frame(frame)
        play_steps.append(call_routine(mpu, meta["play"]))
        snapshots.append(bytes(memory.data[SID_BASE : SID_BASE + SID_SIZE]))
        digest = state_digest(memory, load, len(payload))
        if digest in seen and frame - seen[digest] >= 16:
            loop_start = seen[digest] + 1
            loop_frames = frame - seen[digest]
            break
        seen[digest] = frame

    return {
        "snapshots": snapshots,
        "writes": memory.sid_writes,
        "init_steps": init_steps,
        "play_steps": play_steps,
        "loop_start": loop_start,
        "loop_frames": loop_frames,
    }


def summarize_voice(voice: int, snapshots: list[bytes], writes: list[list[tuple[int, int]]]) -> dict:
    offset = VOICE_OFFSETS[voice]
    events = []
    gate_spans = []
    waveform_changes = []
    gate_attack_frames = []
    gate_release_frames = []
    frequency_change_frames = []
    waveform_frames: dict[str, int] = {}
    noise_write_frames = []
    control_write_counts: dict[str, int] = {}
    previous = bytes(SID_SIZE)
    active_start = None
    active_event = None

    for frame, current in enumerate(snapshots):
        old_control = previous[offset + 4]
        control = current[offset + 4]
        old_gate = old_control & 1
        gate = control & 1
        old_freq = previous[offset] | (previous[offset + 1] << 8)
        freq = current[offset] | (current[offset + 1] << 8)
        controls = [value for register, value in writes[frame] if register == offset + 4]
        for value in controls:
            name = waveform_name(value)
            control_write_counts[name] = control_write_counts.get(name, 0) + 1
        if any((value & 0x81) == 0x81 for value in controls):
            noise_write_frames.append(frame)
        retrigger = any(not (a & 1) and (b & 1) for a, b in zip([old_control] + controls, controls))
        note_changed = nearest_note(freq) != nearest_note(old_freq)
        gate_attack = bool(gate and (not old_gate or retrigger))
        attack = bool(gate_attack or (gate and note_changed))

        waveform = waveform_name(control)
        waveform_frames[waveform] = waveform_frames.get(waveform, 0) + 1
        if gate_attack:
            gate_attack_frames.append(frame)
        if old_gate and not gate:
            gate_release_frames.append(frame)
        if freq != old_freq:
            frequency_change_frames.append(frame)

        if (control & 0xF0) != (old_control & 0xF0):
            waveform_changes.append({"frame": frame, "waveform": waveform_name(control)})

        if attack:
            if active_event is not None:
                active_event["sustain_frames"] = frame - active_event["frame"]
            active_event = {
                "frame": frame,
                "frequency_register": freq,
                "midi": nearest_note(freq),
                "gate_retrigger": retrigger,
                "gate_attack": gate_attack,
                "waveform": waveform,
                "noise": bool(control & 0x80),
            }
            events.append(active_event)
        if gate and not old_gate:
            active_start = frame
        if old_gate and not gate:
            if active_event is not None and "sustain_frames" not in active_event:
                active_event["sustain_frames"] = frame - active_event["frame"]
            if active_start is not None:
                gate_spans.append(frame - active_start)
                active_start = None
        previous = current

    if active_event is not None and "sustain_frames" not in active_event:
        active_event["sustain_frames"] = len(snapshots) - active_event["frame"]
    if active_start is not None:
        gate_spans.append(len(snapshots) - active_start)

    frames = [event["frame"] for event in events]
    intervals = [b - a for a, b in zip(frames, frames[1:])]
    sustains = [event["sustain_frames"] for event in events]
    notes = [event["midi"] for event in events if event["midi"] is not None]
    return {
        "event_count": len(events),
        "note_range": [min(notes), max(notes)] if notes else None,
        "event_frames": frames,
        "gate_attack_frames": gate_attack_frames,
        "gate_attack_cadence": [b - a for a, b in zip(gate_attack_frames, gate_attack_frames[1:])],
        "gate_attack_histogram": histogram([b - a for a, b in zip(gate_attack_frames, gate_attack_frames[1:])]),
        "gate_release_frames": gate_release_frames,
        "frequency_change_frames": frequency_change_frames,
        "frequency_change_histogram": histogram(
            [b - a for a, b in zip(frequency_change_frames, frequency_change_frames[1:])]
        ),
        "cadence_intervals": intervals,
        "cadence_histogram": histogram(intervals),
        "sustain_histogram": histogram(sustains),
        "gate_span_histogram": histogram(gate_spans),
        "noise_hit_frames": [event["frame"] for event in events if event["noise"]],
        "noise_write_frames": noise_write_frames,
        "waveform_frame_counts": waveform_frames,
        "control_write_counts": control_write_counts,
        "waveform_changes": waveform_changes,
        "events": events,
    }


def histogram(values: list[int]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        key = str(value)
        result[key] = result.get(key, 0) + 1
    return dict(sorted(result.items(), key=lambda item: int(item[0])))


def filter_summary(snapshots: list[bytes]) -> dict:
    cutoff = [((state[0x16] << 3) | (state[0x15] & 7)) for state in snapshots]
    resonance_route = [state[0x17] for state in snapshots]
    mode_volume = [state[0x18] for state in snapshots]
    change_frames = [
        frame
        for frame in range(1, len(snapshots))
        if (cutoff[frame], resonance_route[frame], mode_volume[frame] & 0xF0)
        != (cutoff[frame - 1], resonance_route[frame - 1], mode_volume[frame - 1] & 0xF0)
    ]
    return {
        "cutoff_range": [min(cutoff), max(cutoff)] if cutoff else [0, 0],
        "cutoff_median": round(statistics.median(cutoff), 2) if cutoff else 0,
        "change_frames": change_frames,
        "change_interval_histogram": histogram([b - a for a, b in zip(change_frames, change_frames[1:])]),
        "route_values": sorted(set(resonance_route)),
        "mode_values": sorted(set(value & 0xF0 for value in mode_volume)),
    }


def build_report(meta: dict, trace: dict) -> dict:
    snapshots = trace["snapshots"]
    voices = [summarize_voice(i, snapshots, trace["writes"]) for i in range(3)]
    return {
        "metadata": {key: value for key, value in meta.items() if key != "payload"},
        "frames_traced": len(snapshots),
        "duration_seconds": round(len(snapshots) / 50.0, 3),
        "loop_start_frame": trace["loop_start"],
        "loop_frames": trace["loop_frames"],
        "loop_seconds": round(trace["loop_frames"] / 50.0, 3) if trace["loop_frames"] else None,
        "init_cpu_steps": trace["init_steps"],
        "play_cpu_steps": {
            "min": min(trace["play_steps"]),
            "max": max(trace["play_steps"]),
            "median": statistics.median(trace["play_steps"]),
        },
        "voices": voices,
        "filter": filter_summary(snapshots),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sid", type=Path)
    parser.add_argument("--frames", type=int, default=18000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    meta = parse_psid(args.sid)
    report = build_report(meta, trace_psid(meta, args.frames))
    encoded = json.dumps(report, indent=2, ensure_ascii=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="ascii")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
