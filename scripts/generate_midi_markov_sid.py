#!/usr/bin/env python3
"""Transcribe an MP3 to MIDI, learn a Markov loop, and render SID frames.

The checked-in MIDI is the durable intermediate: when the original attachment
is unavailable, a normal build parses that MIDI and regenerates the same
Markov model and three SID voice streams without ffmpeg or NumPy.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import subprocess
from typing import NamedTuple


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MP3 = ROOT / ".context" / "attachments" / "VBKG5Q" / "Voicy_Alice DJ - Better Off Alone (Official Video).mp3"
MIDI_PATH = ROOT / "src" / "music" / "better_off_alone_source.mid"
MODEL_PATH = ROOT / "src" / "music" / "better_off_alone_markov.json"
FRAMES_PATH = ROOT / "src" / "music" / "better_off_alone_frames.bin"
CONSTANTS_PATH = ROOT / "src" / "generated" / "better_off_alone.inc"

SAMPLE_RATE = 22_050
PPQN = 96
STEPS_PER_BEAT = 4
STEP_TICKS = PPQN // STEPS_PER_BEAT
PHRASE_STEPS = 64
FPS = 50
SEED = 0xA11CE
SNARE = 125
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


class MidiStep(NamedTuple):
    lead: int
    bass: int
    drum: int


def decode_mp3(path: Path):
    global np
    try:
        import numpy as np
    except ModuleNotFoundError as error:
        raise SystemExit("NumPy is required to transcribe the MP3") from error
    command = [
        "ffmpeg", "-v", "error", "-i", str(path), "-ac", "1",
        "-ar", str(SAMPLE_RATE), "-f", "f32le", "-",
    ]
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    except FileNotFoundError as error:
        raise SystemExit("ffmpeg is required to transcribe the MP3") from error
    return np.frombuffer(result.stdout, dtype="<f4").astype(np.float64)


def analyse_onsets(samples):
    window_size = 2048
    hop = 256
    window = np.hanning(window_size)
    spectra = []
    for start in range(0, len(samples) - window_size, hop):
        spectra.append(np.abs(np.fft.rfft(samples[start:start + window_size] * window)))
    log_spectra = np.log1p(np.asarray(spectra) * 20.0)
    flux = np.maximum(np.diff(log_spectra, axis=0), 0).sum(axis=1)
    flux = np.maximum(flux - np.median(flux), 0)
    flux /= max(float(flux.max()), 1e-12)
    times = np.arange(len(flux)) * hop / SAMPLE_RATE
    return times, flux


def detect_tempo(samples) -> tuple[float, float]:
    times, flux = analyse_onsets(samples)
    best = (-1.0, 137.0, 0.0)
    for quarter_bpm in range(500, 581):  # 125.00 through 145.00 BPM
        bpm = quarter_bpm / 4.0
        step_seconds = 60.0 / bpm / STEPS_PER_BEAT
        for phase_index in range(32):
            phase = phase_index * step_seconds / 32
            grid = np.arange(phase, len(samples) / SAMPLE_RATE, step_seconds)
            score = float(np.interp(grid, times, flux).sum())
            if score > best[0]:
                best = (score, bpm, phase)
    return best[1], best[2]


def spectral_note_scores(samples, center_seconds: float, low: int, high: int, window_size: int):
    center = int(center_seconds * SAMPLE_RATE)
    start = center - window_size // 2
    block = np.zeros(window_size, dtype=np.float64)
    source_start = max(0, start)
    source_end = min(len(samples), start + window_size)
    block[source_start - start:source_end - start] = samples[source_start:source_end]
    spectrum = np.abs(np.fft.rfft(block * np.hanning(window_size)))
    frequencies = np.fft.rfftfreq(window_size, 1 / SAMPLE_RATE)
    scores = []
    for midi in range(low, high + 1):
        fundamental = 440.0 * 2 ** ((midi - 69) / 12)
        score = 0.0
        for harmonic, weight in ((1, 1.0), (2, 0.45), (3, 0.25), (4, 0.15)):
            target = fundamental * harmonic
            index = int(np.argmin(np.abs(frequencies - target)))
            score += weight * float(spectrum[max(0, index - 1):index + 2].sum())
        scores.append((score, midi))
    scores.sort(reverse=True)
    confidence = scores[0][0] / max(scores[1][0], 1e-12)
    return scores[0][1], confidence


def infer_scale(lead_notes: list[int], bass_notes: list[int]) -> tuple[int, int]:
    scale_intervals = {
        0: (0, 2, 4, 5, 7, 9, 11),
        1: (0, 2, 3, 5, 7, 8, 10),
    }
    bass_counts = Counter(note % 12 for note in bass_notes)
    lead_counts = Counter(note % 12 for note in lead_notes)
    candidates = []
    for tonic in range(12):
        for minor, intervals in scale_intervals.items():
            scale = {(tonic + interval) % 12 for interval in intervals}
            score = sum(count * (1.0 if pc in scale else -0.8) for pc, count in lead_counts.items())
            for pc, count in bass_counts.items():
                relative = (pc - tonic) % 12
                role = {0: 2.5, 7: 1.5, 5: 1.2, 4: 0.8, 3: 0.8}.get(relative, 0.0)
                score += count * (role + (0.7 if pc in scale else -1.0))
            candidates.append((score, tonic, minor))
    _, tonic, minor = max(candidates)
    return tonic, minor


def scale_pcs(tonic: int, minor: int) -> tuple[int, ...]:
    intervals = (0, 2, 3, 5, 7, 8, 10) if minor else (0, 2, 4, 5, 7, 9, 11)
    return tuple((tonic + interval) % 12 for interval in intervals)


def quantize_note(note: int, scale: tuple[int, ...], low: int, high: int) -> int:
    candidates = [value for value in range(low, high + 1) if value % 12 in scale]
    return min(candidates, key=lambda value: (abs(value - note), value))


def transcribe(samples, bpm: float, phase: float) -> tuple[list[MidiStep], dict]:
    step_seconds = 60.0 / bpm / STEPS_PER_BEAT
    total_steps = int((len(samples) / SAMPLE_RATE - phase) / step_seconds)
    raw_lead = []
    lead_confidence = []
    raw_bass = []
    for step in range(total_steps):
        center = phase + (step + 0.5) * step_seconds
        lead, confidence = spectral_note_scores(samples, center, 55, 84, 4096)
        bass, _ = spectral_note_scores(samples, center, 28, 52, 8192)
        raw_lead.append(lead)
        lead_confidence.append(confidence)
        raw_bass.append(bass)

    tonic, minor = infer_scale(raw_lead, raw_bass)
    scale = scale_pcs(tonic, minor)
    confidence_threshold = sorted(lead_confidence)[max(0, len(lead_confidence) // 6)]
    lead_notes = [
        quantize_note(note, scale, 57, 84) if confidence >= confidence_threshold else 0
        for note, confidence in zip(raw_lead, lead_confidence)
    ]

    # Bass is intentionally quantised at quarter-note resolution.  Taking the
    # modal pitch in each beat removes kick harmonics from the transcription.
    bass_notes = [0] * total_steps
    for start in range(0, total_steps, STEPS_PER_BEAT):
        group = raw_bass[start:start + STEPS_PER_BEAT]
        pitch_class = Counter(note % 12 for note in group).most_common(1)[0][0]
        note = min((value for value in range(29, 49) if value % 12 == pitch_class), key=lambda value: abs(value - 40))
        note = quantize_note(note, scale, 29, 48)
        for index in range(start, min(total_steps, start + STEPS_PER_BEAT)):
            bass_notes[index] = note

    steps = []
    for index, (lead, bass) in enumerate(zip(lead_notes, bass_notes)):
        beat = index % 16
        drum = 2 if beat in (0, 8) else (1 if beat in (4, 12) else 0)
        steps.append(MidiStep(lead, bass, drum))
    return steps, {
        "bpm": round(bpm, 2),
        "phase_seconds": round(phase, 4),
        "tonic": tonic,
        "minor": minor,
        "key": f"{NOTE_NAMES[tonic]}{' minor' if minor else ' major'}",
        "source_steps": total_steps,
    }


def variable_length(value: int) -> bytes:
    encoded = [value & 0x7F]
    value >>= 7
    while value:
        encoded.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(encoded))


def midi_track(events: list[tuple[int, int, bytes]], end_tick: int) -> bytes:
    events.sort(key=lambda event: (event[0], event[1]))
    payload = bytearray()
    previous_tick = 0
    for tick, _, message in events:
        payload += variable_length(tick - previous_tick)
        payload += message
        previous_tick = tick
    payload += variable_length(end_tick - previous_tick) + b"\xff\x2f\x00"
    return b"MTrk" + struct.pack(">I", len(payload)) + payload


def note_events(steps: list[MidiStep], field: str, channel: int) -> list[tuple[int, int, bytes]]:
    events = []
    active = 0
    start = 0
    for index in range(len(steps) + 1):
        note = getattr(steps[index], field) if index < len(steps) else 0
        if note == active:
            continue
        tick = index * STEP_TICKS
        if active:
            events.append((tick, 0, bytes((0x80 | channel, active, 0))))
        if note:
            events.append((tick, 1, bytes((0x90 | channel, note, 100))))
        active = note
        start = tick
    return events


def write_midi(path: Path, steps: list[MidiStep], bpm: float) -> None:
    end_tick = len(steps) * STEP_TICKS
    tempo = round(60_000_000 / bpm)
    conductor = [
        (0, 0, b"\xff\x03\x11MP3 transcription"),
        (0, 1, b"\xff\x51\x03" + tempo.to_bytes(3, "big")),
        (0, 2, b"\xff\x58\x04\x04\x02\x18\x08"),
    ]
    lead = [(0, 0, b"\xff\x03\x04Lead")] + note_events(steps, "lead", 0)
    bass = [(0, 0, b"\xff\x03\x04Bass")] + note_events(steps, "bass", 1)
    drums = [(0, 0, b"\xff\x03\x05Drums")]
    for index, step in enumerate(steps):
        note = 36 if step.drum == 2 else (38 if step.drum == 1 else 0)
        if note:
            tick = index * STEP_TICKS
            drums.append((tick, 1, bytes((0x99, note, 100))))
            drums.append((tick + STEP_TICKS // 2, 0, bytes((0x89, note, 0))))
    tracks = [
        midi_track(conductor, end_tick), midi_track(lead, end_tick),
        midi_track(bass, end_tick), midi_track(drums, end_tick),
    ]
    header = b"MThd" + struct.pack(">IHHH", 6, 1, len(tracks), PPQN)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + b"".join(tracks))


def read_variable(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    while True:
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, offset


def parse_midi(path: Path) -> tuple[list[MidiStep], float]:
    data = path.read_bytes()
    if data[:4] != b"MThd" or int.from_bytes(data[12:14], "big") != PPQN:
        raise SystemExit(f"unsupported MIDI format: {path}")
    track_count = int.from_bytes(data[10:12], "big")
    offset = 14
    intervals: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    drums: dict[int, int] = {}
    tempo = 60_000_000 / 137.0
    maximum_tick = 0
    for _ in range(track_count):
        if data[offset:offset + 4] != b"MTrk":
            raise SystemExit(f"invalid MIDI track in {path}")
        length = int.from_bytes(data[offset + 4:offset + 8], "big")
        track = data[offset + 8:offset + 8 + length]
        offset += 8 + length
        position = 0
        tick = 0
        active: dict[tuple[int, int], int] = {}
        while position < len(track):
            delta, position = read_variable(track, position)
            tick += delta
            maximum_tick = max(maximum_tick, tick)
            status = track[position]
            position += 1
            if status == 0xFF:
                meta_type = track[position]
                position += 1
                size, position = read_variable(track, position)
                payload = track[position:position + size]
                position += size
                if meta_type == 0x51:
                    tempo = int.from_bytes(payload, "big")
                continue
            kind = status & 0xF0
            channel = status & 0x0F
            note = track[position]
            velocity = track[position + 1]
            position += 2
            if kind == 0x90 and velocity:
                if channel == 9:
                    drums[tick // STEP_TICKS] = 2 if note == 36 else 1
                else:
                    active[(channel, note)] = tick
            elif kind == 0x80 or (kind == 0x90 and velocity == 0):
                start = active.pop((channel, note), None)
                if start is not None:
                    intervals[channel].append((start, tick, note))

    total_steps = math.ceil(maximum_tick / STEP_TICKS)
    lead = [0] * total_steps
    bass = [0] * total_steps
    for channel, destination in ((0, lead), (1, bass)):
        for start, end, note in intervals[channel]:
            for step in range(start // STEP_TICKS, min(total_steps, math.ceil(end / STEP_TICKS))):
                destination[step] = note
    steps = [MidiStep(lead[i], bass[i], drums.get(i, 0)) for i in range(total_steps)]
    return steps, 60_000_000 / tempo


def build_markov(steps: list[MidiStep], metadata: dict) -> dict:
    states: list[MidiStep] = []
    indices: dict[MidiStep, int] = {}
    sequence = []
    for state in steps:
        if state not in indices:
            indices[state] = len(states)
            states.append(state)
        sequence.append(indices[state])

    transitions: dict[tuple[int, int], Counter] = defaultdict(Counter)
    first_order: dict[int, Counter] = defaultdict(Counter)
    for index in range(2, len(sequence)):
        transitions[(sequence[index - 2], sequence[index - 1])][sequence[index]] += 1
        first_order[sequence[index - 1]][sequence[index]] += 1
    # Explicit circular phrase edges make the learned graph loopable.
    for start in range(0, len(sequence) - PHRASE_STEPS + 1, PHRASE_STEPS):
        phrase = sequence[start:start + PHRASE_STEPS]
        for index in range(PHRASE_STEPS):
            transitions[(phrase[index - 2], phrase[index - 1])][phrase[index]] += 2
            first_order[phrase[index - 1]][phrase[index]] += 2

    encoded = {
        f"{first},{second}": {str(target): count for target, count in sorted(counts.items())}
        for (first, second), counts in sorted(transitions.items())
    }
    return {
        "format": 1,
        "seed": SEED,
        "metadata": metadata,
        "states": [state._asdict() for state in states],
        "midi_sequence": sequence,
        "order": 2,
        "transitions": encoded,
        "first_order_backoff": {
            str(source): {str(target): count for target, count in sorted(counts.items())}
            for source, counts in sorted(first_order.items())
        },
    }


def weighted_choice(rng: random.Random, counts: Counter) -> int:
    target = rng.randrange(sum(counts.values()))
    for value, weight in sorted(counts.items()):
        if target < weight:
            return value
        target -= weight
    raise AssertionError("empty Markov transition")


def generate_loop(model: dict) -> list[MidiStep]:
    source = model["midi_sequence"]
    start = PHRASE_STEPS if len(source) >= PHRASE_STEPS * 2 else 0
    generated = source[start:start + 2]
    transitions = {
        tuple(map(int, key.split(","))): Counter({int(k): v for k, v in counts.items()})
        for key, counts in model["transitions"].items()
    }
    first_order = {
        int(source): Counter({int(target): count for target, count in counts.items()})
        for source, counts in model["first_order_backoff"].items()
    }
    global_counts = Counter(source)
    rng = random.Random(model["seed"])

    def choices(context: tuple[int, int]) -> Counter:
        # Observed second-order motion dominates, while a lighter first-order
        # backoff lets repeated MIDI phrases recombine instead of replaying as
        # a literal tape loop.
        combined = Counter(first_order.get(context[1], global_counts))
        for target, count in transitions.get(context, {}).items():
            combined[target] += count * 2
        return combined

    while len(generated) < PHRASE_STEPS - 2:
        generated.append(weighted_choice(rng, choices(tuple(generated[-2:]))))

    # Pick a two-state Markov bridge that has valid edges back through the
    # opening pair.  This makes the 64-step generated walk a genuine cycle.
    context = tuple(generated[-2:])
    first, second = generated[0], generated[1]
    best = None
    for penultimate, count_a in choices(context).items():
        for final, count_b in choices((context[1], penultimate)).items():
            close_a = choices((penultimate, final)).get(first, 0)
            close_b = choices((final, first)).get(second, 0)
            score = count_a * count_b * close_a * close_b
            if score and (best is None or score > best[0]):
                best = (score, penultimate, final)
    if best is None:
        # The circular training edges guarantee a safe observed fallback.
        phrase = source[start:start + PHRASE_STEPS]
        generated = phrase
    else:
        generated.extend(best[1:])
    model["generated_sequence"] = generated
    return [MidiStep(**model["states"][index]) for index in generated]


def diatonic_triad(root_note: int, tonic: int, minor: int) -> tuple[int, int, int]:
    scale = scale_pcs(tonic, minor)
    root_pc = min(scale, key=lambda pc: min((pc - root_note) % 12, (root_note - pc) % 12))
    index = scale.index(root_pc)
    return tuple(scale[(index + offset) % 7] for offset in (0, 2, 4))


def nearest_midi(pitch_class: int, target: int, low: int, high: int) -> int:
    return min((note for note in range(low, high + 1) if note % 12 == pitch_class), key=lambda note: abs(note - target))


def render_sid(loop: list[MidiStep], metadata: dict) -> tuple[bytes, int]:
    bpm = float(metadata["bpm"])
    frames = round(PHRASE_STEPS * FPS * 60 / (bpm * STEPS_PER_BEAT))
    boundaries = [round(step * frames / PHRASE_STEPS) for step in range(PHRASE_STEPS + 1)]
    lead = [0] * frames
    arp = [0] * frames
    bass = [0] * frames
    previous_lead = 0
    previous_bass = 0
    harmonic_bass = loop[0].bass
    arp_rest = True
    for step, state in enumerate(loop):
        start, end = boundaries[step], boundaries[step + 1]
        if step % STEPS_PER_BEAT == 0 and state.bass:
            harmonic_bass = state.bass
        beat = step % 16
        drum = 2 if beat in (0, 8) else (1 if beat in (4, 12) else 0)
        if state.lead:
            retrigger = state.lead != previous_lead or step % 16 == 0
            for frame in range(start, end):
                lead[frame] = state.lead | (0x80 if frame == start and retrigger else 0)
            previous_lead = state.lead
        else:
            previous_lead = 0

        if harmonic_bass:
            chord = diatonic_triad(harmonic_bass, int(metadata["tonic"]), int(metadata["minor"]))
            for frame in range(start, end):
                tone = (0, 1, 2, 1)[(frame // 3) % 4]
                note = nearest_midi(chord[tone], 60, 48, 72)
                retrigger = frame == start and (arp_rest or step % 4 == 0)
                arp[frame] = note | (0x80 if retrigger else 0)
            arp_rest = False
        else:
            arp_rest = True

        if drum == 1:
            length = min(3, end - start)
            bass[start] = SNARE | 0x80
            for frame in range(start + 1, start + length):
                bass[frame] = SNARE
            previous_bass = 0
        elif harmonic_bass:
            retrigger = harmonic_bass != previous_bass or drum == 2 or step % 8 == 0
            for frame in range(start, end):
                bass[frame] = harmonic_bass | (0x80 if frame == start and retrigger else 0)
            if drum == 2 and end - start >= 3:
                bass[start + 1] = min(harmonic_bass + 12, 60)
                bass[start + 2] = min(harmonic_bass + 7, 55)
            previous_bass = harmonic_bass
    return bytes(lead + arp + bass), frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_MP3)
    parser.add_argument("--midi", type=Path, default=MIDI_PATH)
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    args = parser.parse_args()

    if args.input.exists():
        samples = decode_mp3(args.input)
        bpm, phase = detect_tempo(samples)
        steps, metadata = transcribe(samples, bpm, phase)
        metadata.update({
            "input": args.input.name,
            "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
            "duration_seconds": round(len(samples) / SAMPLE_RATE, 3),
        })
        write_midi(args.midi, steps, bpm)
    elif not args.midi.exists():
        raise SystemExit(f"missing MP3 ({args.input}) and MIDI ({args.midi})")

    midi_steps, midi_bpm = parse_midi(args.midi)
    if not args.input.exists():
        if args.model.exists():
            metadata = json.loads(args.model.read_text())["metadata"]
        else:
            tonic, minor = infer_scale(
                [state.lead for state in midi_steps if state.lead],
                [state.bass for state in midi_steps if state.bass],
            )
            metadata = {"bpm": round(midi_bpm, 2), "tonic": tonic, "minor": minor, "key": f"{NOTE_NAMES[tonic]}{' minor' if minor else ' major'}"}
    metadata["bpm"] = round(midi_bpm, 2)
    model = build_markov(midi_steps, metadata)
    loop = generate_loop(model)
    frame_data, loop_frames = render_sid(loop, metadata)
    if len(loop) != PHRASE_STEPS or len(frame_data) != loop_frames * 3:
        raise AssertionError("invalid generated loop size")

    model["loop"] = {
        "steps": PHRASE_STEPS,
        "frames": loop_frames,
        "seconds": round(loop_frames / FPS, 3),
        "seam_context": model["generated_sequence"][-2:] + model["generated_sequence"][:2],
    }
    args.model.parent.mkdir(parents=True, exist_ok=True)
    args.model.write_text(json.dumps(model, indent=2) + "\n")
    FRAMES_PATH.write_bytes(frame_data)
    CONSTANTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONSTANTS_PATH.write_text(f"; Generated by scripts/generate_midi_markov_sid.py\nBETTER_LOOP_FRAMES = {loop_frames}\n")
    print(f"Transcribed {len(midi_steps)} MIDI steps at {midi_bpm:.2f} BPM in {metadata['key']}")
    print(f"Generated closed order-2 Markov loop: {PHRASE_STEPS} steps / {loop_frames} PAL frames / {loop_frames / FPS:.2f}s")
    print(f"Wrote {args.midi.resolve().relative_to(ROOT)}, {args.model.resolve().relative_to(ROOT)}, and {FRAMES_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
