#!/usr/bin/env python3
"""Compose "Dark Armada", an original motif-Markov SID military cue.

The tune uses a deterministic second-order Markov chain over complete,
original one-bar motifs. Keeping the learned state at phrase level produces
recognisable development instead of disconnected note choices. The musical
language is dark G minor with dotted rhythms, chromatic tension, pedal tones,
and triadic leaps; no existing film or game melody is transcribed.

The arrangement uses only three SID voices. Three 83.33 BPM bars establish pulse
stabs and a half-time beat with no lead. Four 93.75 BPM bars reveal fragments
of the generated melody. Twelve 107 BPM bars deliver the full march with a
saw-to-pulse lead, rapid arpeggios, and a bass voice time-shared with kick and
noise snare. The generated frame format is 0 for gate off, bit 7 for a hard
restart, and a plain MIDI note value for a held gate.
"""

import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRAMES_BIN = ROOT / "src" / "music" / "imperial_march_frames.bin"
CHAIN_JSON = ROOT / "src" / "music" / "imperial_march_markov.json"
INC_PATH = ROOT / "src" / "generated" / "imperial_march.inc"

SLOTS_PER_BAR = 16
PAL_FRAMES_PER_SECOND = 50
START_TRIM_SECONDS = 8
START_TRIM_FRAMES = START_TRIM_SECONDS * PAL_FRAMES_PER_SECOND
INTRO_BARS = 3
BUILD_BARS = 4
MARCH_BARS = 12
TOTAL_BARS = INTRO_BARS + BUILD_BARS + MARCH_BARS
MARCH_START = INTRO_BARS + BUILD_BARS
BAR_SLOT_FRAMES = (9,) * INTRO_BARS + (8,) * BUILD_BARS + (7,) * MARCH_BARS
SEED = 0xD4A64

SNARE_PITCH = 125
KICK_PITCH = 126
NOTE_OFFSETS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name: str) -> int:
    letter = name[0]
    rest = name[1:]
    accidental = 0
    if rest.startswith("#"):
        accidental, rest = 1, rest[1:]
    elif rest.startswith("b"):
        accidental, rest = -1, rest[1:]
    return 12 * (int(rest) + 1) + NOTE_OFFSETS[letter] + accidental


BASE_NOTE = midi("G4")


def motif(*events):
    if sum(duration for _, duration in events) != SLOTS_PER_BAR:
        raise ValueError(f"motif must fill one bar: {events}")
    return list(events)


# Semitone offsets from G4. None is a musical rest. Each motif is original
# and deliberately distinct in rhythm and contour.
MOTIFS = {
    "iron": motif((0, 2), (7, 1), (3, 1), (2, 2), (-2, 2), (0, 4), (5, 2), (3, 2)),
    "fall": motif((7, 2), (5, 1), (3, 1), (2, 2), (0, 2), (-2, 2), (-4, 2), (-5, 2), (-7, 2)),
    "signal": motif((None, 2), (0, 2), (3, 1), (5, 1), (7, 2), (10, 2), (7, 2), (5, 2), (3, 2)),
    "answer": motif((3, 2), (2, 2), (0, 1), (-2, 1), (-4, 2), (0, 2), (2, 2), (3, 2), (7, 2)),
    "climb": motif((-7, 2), (-4, 2), (0, 2), (3, 2), (7, 2), (10, 2), (8, 2), (7, 2)),
    "stomp": motif((0, 3), (3, 1), (7, 2), (5, 2), (3, 3), (2, 1), (0, 4)),
    "shadow": motif((None, 2), (-5, 2), (0, 2), (-2, 1), (-4, 1), (-5, 4), (-2, 2), (0, 2)),
    "blade": motif((12, 1), (10, 1), (7, 2), (5, 1), (3, 1), (2, 2), (7, 2), (5, 2), (3, 2), (0, 2)),
}

CADENCE = motif((-1, 2), (2, 2), (-5, 2), (-1, 2), (0, 8))

# These phrase orders are the training corpus. The chain learns which motifs
# can follow pairs of motifs, then creates a different deterministic route.
TRAINING_SEQUENCES = (
    ("iron", "shadow", "signal", "fall", "stomp", "answer", "climb", "blade"),
    ("signal", "answer", "iron", "fall", "shadow", "climb", "stomp", "blade"),
    ("stomp", "iron", "answer", "shadow", "signal", "blade", "fall", "climb"),
    ("shadow", "fall", "iron", "climb", "answer", "stomp", "signal", "blade"),
)

CHORD_NAMES = (
    ("G3", "Bb3", "D4"), ("Eb3", "G3", "Bb3"),
    ("D3", "F#3", "A3"),
    ("G3", "Bb3", "D4"), ("C3", "Eb3", "G3"),
    ("Eb3", "G3", "Bb3"), ("D3", "F#3", "A3"),
    ("G3", "Bb3", "D4"), ("Eb3", "G3", "Bb3"),
    ("Bb2", "D3", "F3"), ("D3", "F#3", "A3"),
    ("G3", "Bb3", "D4"), ("C3", "Eb3", "G3"),
    ("Eb3", "G3", "Bb3"), ("D3", "F#3", "A3"),
    ("G3", "Bb3", "D4"), ("Eb3", "G3", "Bb3"),
    ("D3", "F#3", "A3"), ("G3", "Bb3", "D4"),
)
ARP_CHORDS = tuple(tuple(midi(note) for note in chord) for chord in CHORD_NAMES)
BASS_ROOTS = tuple(midi(note) for note in (
    "G1", "Eb1", "D2", "G1", "C2", "Eb1", "D2", "G1", "Eb1",
    "Bb1", "D2", "G1", "C2", "Eb1", "D2", "G1", "Eb1", "D2", "G1",
))
REGISTER_SHIFTS = (-12, -12, 0, 0, 0, 0, 12, 0, 0, -12, 0, 12, 0, 0, 12)


def train_chain(sequences):
    order2 = {}
    order1 = {}
    for sequence in sequences:
        wrapped = sequence + sequence[:2]
        for index in range(len(sequence)):
            a, b, nxt = wrapped[index:index + 3]
            order2.setdefault((a, b), []).append(nxt)
            order1.setdefault(b, []).append(nxt)
    return order2, order1


def generate_motif_sequence(order2, order1, count: int, rng):
    result = ["iron", "shadow"]
    used_trigrams = set()
    while len(result) < count:
        state = (result[-2], result[-1])
        strict = order2.get(state, [])
        backoff = order1.get(result[-1], [])
        # Occasional first-order backoff creates a new route without breaking
        # the learned phrase-to-phrase vocabulary.
        if backoff and rng.random() < 0.75:
            choices = list(backoff)
        else:
            choices = list(strict or backoff or MOTIFS)
        fresh = [name for name in choices
                 if (result[-2], result[-1], name) not in used_trigrams]
        if fresh:
            choices = fresh
        moving = [name for name in choices if name != result[-1]]
        if moving:
            choices = moving
        chosen = rng.choice(choices)
        used_trigrams.add((result[-2], result[-1], chosen))
        result.append(chosen)
    return result


def transpose_motif(events, semitones: int):
    return [(None if offset is None else BASE_NOTE + offset + semitones, duration)
            for offset, duration in events]


def stage_lead(events, bar: int):
    if bar < INTRO_BARS:
        return [(None, SLOTS_PER_BAR)]
    if bar == INTRO_BARS:
        keep = {0, len(events) - 1}
    elif bar == INTRO_BARS + 1:
        keep = set(range(0, len(events), 3))
    elif bar < MARCH_START:
        keep = set(range(0, len(events), 2))
    else:
        return events
    return [(pitch if index in keep else None, duration)
            for index, (pitch, duration) in enumerate(events)]


def render_events(events, gap_frames: int, frames_per_16th: int) -> bytearray:
    output = bytearray()
    for pitch, sixteenths in events:
        frames = sixteenths * frames_per_16th
        if pitch is None:
            output += bytes(frames)
            continue
        hold = frames - 1 - gap_frames
        output += bytes([pitch | 0x80]) + bytes([pitch] * hold) + bytes(gap_frames)
    return output


def backing_bar(chord, bar: int):
    if bar < INTRO_BARS:
        return [(chord[0], 6), (None, 2), (chord[2], 4), (None, 4)]
    if bar < MARCH_START:
        pattern = (0, 2, 1, 2, 0, 1, 2, 1)
        return [(chord[index], 2) for index in pattern]
    patterns = (
        (0, 1, 2, 1, 0, 2, 1, 2, 0, 1, 2, 1, 2, 1, 0, 1),
        (0, 2, 1, 2, 0, 1, 2, 1, 0, 2, 1, 2, 1, 0, 2, 1),
        (2, 1, 0, 1, 2, 0, 1, 0, 2, 1, 0, 1, 0, 1, 2, 1),
        (0, 1, 2, 0, 1, 2, 1, 0, 2, 1, 2, 0, 1, 0, 2, 1),
    )
    return [(chord[index], 1) for index in patterns[bar & 3]]


def rhythm_bar(root: int, bar: int):
    if bar < INTRO_BARS:
        return [
            (KICK_PITCH, 2), (root, 2), (None, 4),
            (SNARE_PITCH, 2), (root + 12, 2), (None, 4),
        ]
    if bar < MARCH_START:
        return [
            (KICK_PITCH, 2), (root, 2), (SNARE_PITCH, 2), (root + 12, 2),
            (KICK_PITCH, 2), (root, 1), (root, 1), (SNARE_PITCH, 2), (root, 2),
        ]
    head = [
        (KICK_PITCH, 2), (root, 1), (root, 1),
        (SNARE_PITCH, 2), (root + 12, 2), (KICK_PITCH, 2),
    ]
    if bar in {10, 14, 18}:
        return head + [(SNARE_PITCH, 1)] * 6
    return head + [
        (root, 1), (root, 1), (SNARE_PITCH, 1), (SNARE_PITCH, 1), (root, 2),
    ]


def main() -> None:
    order2, order1 = train_chain(TRAINING_SEQUENCES)
    rng = random.Random(SEED)
    motif_names = generate_motif_sequence(
        order2, order1, TOTAL_BARS - INTRO_BARS - 1, rng)

    lead_bars = []
    for index in range(TOTAL_BARS):
        if index == TOTAL_BARS - 1:
            lead_bars.append(transpose_motif(CADENCE, 0))
            continue
        motif_index = max(0, index - INTRO_BARS)
        shift = REGISTER_SHIFTS[motif_index]
        lead_bars.append(transpose_motif(MOTIFS[motif_names[motif_index]], shift))

    lead = bytearray()
    backing = bytearray()
    rhythm = bytearray()
    for bar, (lead_events, chord, root, slot_frames) in enumerate(zip(
            lead_bars, ARP_CHORDS, BASS_ROOTS, BAR_SLOT_FRAMES)):
        lead_gap = 2 if bar < MARCH_START else 0
        lead += render_events(stage_lead(lead_events, bar), lead_gap, slot_frames)
        backing += render_events(backing_bar(chord, bar), 1, slot_frames)
        rhythm += render_events(rhythm_bar(root, bar), 2, slot_frames)

    rendered_frames = SLOTS_PER_BAR * sum(BAR_SLOT_FRAMES)
    if not all(len(stream) == rendered_frames for stream in (lead, backing, rhythm)):
        raise RuntimeError("generated voice streams do not have equal loop lengths")

    lead = lead[START_TRIM_FRAMES:]
    backing = backing[START_TRIM_FRAMES:]
    rhythm = rhythm[START_TRIM_FRAMES:]
    loop_frames = rendered_frames - START_TRIM_FRAMES

    FRAMES_BIN.write_bytes(lead + backing + rhythm)
    CHAIN_JSON.write_text(json.dumps({
        "seed": SEED,
        "start_trim_frames": START_TRIM_FRAMES,
        "start_trim_seconds": START_TRIM_SECONDS,
        "order2": {f"{a}|{b}": values for (a, b), values in sorted(order2.items())},
        "order1": dict(sorted(order1.items())),
        "motif_sequence": motif_names + ["cadence"],
        "bar_slot_frames": [*BAR_SLOT_FRAMES],
        "register_shifts": [*REGISTER_SHIFTS],
        "motifs": {name: [[offset, duration] for offset, duration in events]
                   for name, events in MOTIFS.items()},
    }, indent=1) + "\n", encoding="ascii")
    INC_PATH.write_text(
        "; Generated by scripts/generate_imperial_markov_sid.py.\n"
        f"IMPERIAL_LOOP_FRAMES = {loop_frames}\n",
        encoding="ascii",
    )
    print(f"Wrote {FRAMES_BIN.relative_to(ROOT)} "
          f"({loop_frames} frames/voice, {loop_frames / 50:.2f}s loop)")
    print(f"Motif Markov route: {' -> '.join(motif_names)} -> cadence")
    print(f"Wrote {CHAIN_JSON.relative_to(ROOT)}")
    print(f"Wrote {INC_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
