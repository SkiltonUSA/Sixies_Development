#!/usr/bin/env python3
"""Compose "Gearshift", an original punchy motif-Markov SID tune.

The deterministic second-order Markov chain is trained on short, original
one-bar hook motifs rather than individual notes.  That keeps the generated
route surprising without losing the repetition and call/response structure a
game tune needs.  The output format is one byte per PAL frame per SID voice:
0 gates a voice off, bit 7 requests a hard restart, and bits 0-6 hold a MIDI
note number.

The musical vocabulary uses brisk minor-key hooks, clipped pulse arpeggios,
octave bass, pitch-drop kicks, noise snares, and short turnaround fills.  It
evokes the energetic British C64 game-score tradition without transcribing or
reworking an existing composition.
"""

import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRAMES_BIN = ROOT / "src" / "music" / "gearshift_markov_frames.bin"
CHAIN_JSON = ROOT / "src" / "music" / "gearshift_markov_chain.json"
INC_PATH = ROOT / "src" / "generated" / "gearshift_markov.inc"

SLOTS_PER_BAR = 16
FRAMES_PER_16TH = 6
BAR_FRAMES = SLOTS_PER_BAR * FRAMES_PER_16TH
TOTAL_BARS = 16
SEED = 0xB3D4615

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


BASE_NOTE = midi("D5")


def motif(*events):
    if sum(duration for _, duration in events) != SLOTS_PER_BAR:
        raise ValueError(f"motif must fill one bar: {events}")
    return list(events)


# Semitone offsets from D5. None is a rest. These are deliberately compact:
# each has a distinct rhythmic fingerprint that can work as a reusable hook.
MOTIFS = {
    "spark": motif((0, 2), (7, 1), (12, 1), (10, 2), (7, 2),
                   (3, 2), (5, 1), (7, 1), (0, 4)),
    "answer": motif((3, 2), (5, 2), (7, 1), (5, 1), (3, 2),
                    (0, 2), (-2, 2), (0, 4)),
    "ratchet": motif((0, 1), (0, 1), (7, 1), (0, 1), (10, 2),
                     (7, 1), (5, 1), (3, 2), (0, 2), (-2, 2), (0, 2)),
    "vault": motif((0, 2), (3, 1), (7, 1), (12, 2), (10, 1), (7, 1),
                   (15, 2), (12, 2), (10, 2), (7, 2)),
    "skip": motif((None, 1), (0, 1), (3, 2), (7, 1), (10, 1),
                  (7, 2), (5, 1), (3, 1), (0, 2), (7, 2), (5, 2)),
    "drop": motif((12, 2), (10, 1), (7, 1), (5, 2), (3, 2),
                  (0, 2), (-2, 1), (-4, 1), (-5, 4)),
    "switch": motif((0, 3), (7, 1), (10, 2), (3, 2), (5, 3),
                    (12, 1), (10, 2), (7, 2)),
    "chase": motif((-5, 1), (0, 1), (3, 1), (5, 1), (7, 2),
                   (5, 1), (3, 1), (0, 2), (3, 1), (5, 1), (7, 4)),
}

CADENCE = motif((0, 1), (3, 1), (7, 2), (12, 2), (10, 2),
                (7, 2), (5, 2), (0, 4))

# Phrase-order training data. The generated tune learns transitions between
# complete motifs; it does not ingest any external song or copyrighted MIDI.
TRAINING_SEQUENCES = (
    ("spark", "answer", "ratchet", "vault", "spark", "skip", "drop", "chase"),
    ("spark", "ratchet", "switch", "answer", "skip", "vault", "drop", "chase"),
    ("ratchet", "vault", "spark", "answer", "switch", "skip", "chase", "drop"),
    ("skip", "answer", "spark", "vault", "ratchet", "switch", "drop", "chase"),
)

CHORD_NAMES = (
    ("D3", "F3", "A3"), ("Bb2", "D3", "F3"),
    ("C3", "E3", "G3"), ("A2", "C#3", "E3"),
    ("D3", "F3", "A3"), ("G2", "Bb2", "D3"),
    ("Bb2", "D3", "F3"), ("A2", "C#3", "E3"),
    ("D3", "F3", "A3"), ("C3", "E3", "G3"),
    ("Bb2", "D3", "F3"), ("A2", "C#3", "E3"),
    ("G2", "Bb2", "D3"), ("Bb2", "D3", "F3"),
    ("A2", "C#3", "E3"), ("D3", "F3", "A3"),
)
ARP_CHORDS = tuple(tuple(midi(note) for note in chord) for chord in CHORD_NAMES)
BASS_ROOTS = tuple(midi(note) for note in (
    "D2", "Bb1", "C2", "A1", "D2", "G1", "Bb1", "A1",
    "D2", "C2", "Bb1", "A1", "G1", "Bb1", "A1", "D2",
))
REGISTER_SHIFTS = (0, 0, 0, 0, 0, 0, 12, 0, 0, 0, -12, 0, 0, 12, 0)


def train_chain(sequences):
    order2 = {}
    order1 = {}
    for sequence in sequences:
        wrapped = sequence + sequence[:2]
        for index in range(len(sequence)):
            first, second, following = wrapped[index:index + 3]
            order2.setdefault((first, second), []).append(following)
            order1.setdefault(second, []).append(following)
    return order2, order1


def weighted_choice(choices, rng):
    """Choose from the transition multiset, preserving learned frequency."""
    return choices[rng.randrange(len(choices))]


def generate_route(order2, order1, count, rng):
    route = ["spark", "answer"]
    used_trigrams = set()
    while len(route) < count:
        state = (route[-2], route[-1])
        strict = order2.get(state, [])
        backoff = order1.get(route[-1], [])
        choices = list(strict)
        # Controlled first-order backoff occasionally opens a new branch while
        # retaining the learned motif-to-motif musical grammar.
        if backoff and (not choices or rng.random() < 0.28):
            choices = list(backoff)
        if not choices:
            choices = list(MOTIFS)
        fresh = [choice for choice in choices
                 if (route[-2], route[-1], choice) not in used_trigrams]
        if fresh:
            choices = fresh
        chosen = weighted_choice(choices, rng)
        used_trigrams.add((route[-2], route[-1], chosen))
        route.append(chosen)
    return route


def transpose(events, semitones):
    return [(None if offset is None else BASE_NOTE + offset + semitones, duration)
            for offset, duration in events]


def render_events(events, gap_frames):
    output = bytearray()
    for pitch, sixteenths in events:
        frames = sixteenths * FRAMES_PER_16TH
        if pitch is None:
            output += bytes(frames)
            continue
        hold = frames - 1 - gap_frames
        output += bytes([pitch | 0x80]) + bytes([pitch] * hold) + bytes(gap_frames)
    return output


ARP_PATTERNS = (
    (0, 1, 2, 1, 0, 1, 2, 1, 0, 2, 1, 2, 0, 1, 2, 1),
    (0, 2, 1, 2, 0, 1, 2, 1, 0, 2, 1, 0, 2, 1, 2, 1),
    (2, 1, 0, 1, 2, 0, 1, 0, 2, 1, 0, 1, 2, 0, 1, 0),
    (0, 1, 2, 0, 1, 2, 1, 0, 2, 1, 0, 2, 1, 2, 0, 1),
)


def arp_bar(chord, bar_index):
    pattern = ARP_PATTERNS[bar_index & 3]
    # Lift occasional top notes to make the accompaniment flash without
    # stealing the lead voice.
    return [(chord[index] + (12 if slot in {7, 15} else 0), 1)
            for slot, index in enumerate(pattern)]


def rhythm_bar(root, bar_index):
    if bar_index in {3, 7, 11, 15}:
        return [
            (KICK_PITCH, 2), (root, 1), (root + 12, 1),
            (SNARE_PITCH, 2), (root, 2), (KICK_PITCH, 2),
        ] + [(SNARE_PITCH, 1)] * 6
    if bar_index >= 8:
        return [
            (KICK_PITCH, 2), (root, 1), (root + 12, 1),
            (SNARE_PITCH, 2), (root, 1), (root + 12, 1),
            (KICK_PITCH, 2), (root, 1), (SNARE_PITCH, 1),
            (root + 12, 2), (SNARE_PITCH, 1), (root, 1),
        ]
    return [
        (KICK_PITCH, 2), (root, 1), (root + 12, 1),
        (SNARE_PITCH, 2), (root, 2), (KICK_PITCH, 2),
        (root + 12, 2), (SNARE_PITCH, 2), (root, 2),
    ]


def main():
    order2, order1 = train_chain(TRAINING_SEQUENCES)
    route = generate_route(order2, order1, TOTAL_BARS - 1, random.Random(SEED))

    lead = bytearray()
    arp = bytearray()
    rhythm = bytearray()
    for bar_index, (chord, root) in enumerate(zip(ARP_CHORDS, BASS_ROOTS)):
        if bar_index == TOTAL_BARS - 1:
            lead_events = transpose(CADENCE, 0)
        else:
            lead_events = transpose(
                MOTIFS[route[bar_index]], REGISTER_SHIFTS[bar_index])
        lead += render_events(lead_events, gap_frames=0)
        arp += render_events(arp_bar(chord, bar_index), gap_frames=1)
        rhythm += render_events(rhythm_bar(root, bar_index), gap_frames=1)

    loop_frames = TOTAL_BARS * BAR_FRAMES
    if not all(len(stream) == loop_frames for stream in (lead, arp, rhythm)):
        raise RuntimeError("generated voice streams do not have equal loop lengths")

    FRAMES_BIN.write_bytes(lead + arp + rhythm)
    CHAIN_JSON.write_text(json.dumps({
        "seed": SEED,
        "order": 2,
        "tempo_bpm": 50 * 60 / (4 * FRAMES_PER_16TH),
        "frames_per_16th": FRAMES_PER_16TH,
        "training_sequences": TRAINING_SEQUENCES,
        "order2": {f"{a}|{b}": values
                   for (a, b), values in sorted(order2.items())},
        "order1_backoff": dict(sorted(order1.items())),
        "generated_route": route + ["cadence"],
        "register_shifts": REGISTER_SHIFTS,
        "motifs": {name: [[offset, duration] for offset, duration in events]
                   for name, events in MOTIFS.items()},
    }, indent=1) + "\n", encoding="ascii")
    INC_PATH.parent.mkdir(parents=True, exist_ok=True)
    INC_PATH.write_text(
        "; Generated by scripts/generate_gearshift_markov_sid.py.\n"
        f"GEARSHIFT_LOOP_FRAMES = {loop_frames}\n",
        encoding="ascii",
    )
    print(f"Wrote {FRAMES_BIN.relative_to(ROOT)} "
          f"({loop_frames} frames/voice, {loop_frames / 50:.2f}s, 125 BPM)")
    print(f"Second-order Markov route: {' -> '.join(route)} -> cadence")
    print(f"Wrote {CHAIN_JSON.relative_to(ROOT)}")
    print(f"Wrote {INC_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
