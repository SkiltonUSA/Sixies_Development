#!/usr/bin/env python3
"""Generate a hand-arranged 40-second three-voice SID frame set.

The previous MP3-to-MIDI transcription was too dense for a three-voice SID
player. This generator writes deliberate 50 Hz note streams: lead, arpeggio
root, and bass/percussion.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "music" / "starwars_3voice_frames.bin"

FPS = 50
FRAMES = 40 * FPS
EIGHTH = 15
QUARTER = EIGHTH * 2
BAR = QUARTER * 4

NOTES = {
    "C": 0,
    "CS": 1,
    "D": 2,
    "DS": 3,
    "E": 4,
    "F": 5,
    "FS": 6,
    "G": 7,
    "GS": 8,
    "A": 9,
    "AS": 10,
    "B": 11,
}


def midi(name: str) -> int:
    if name == "R":
        return 0
    pitch = name[:-1].upper()
    octave = int(name[-1])
    return (octave + 1) * 12 + NOTES[pitch]


def place_note(track: list[int], start: int, pitch: int, length: int) -> None:
    if pitch <= 0 or start >= FRAMES:
        return
    end = min(FRAMES, start + length)
    track[start] = pitch | 0x80
    for frame in range(start + 1, end):
        track[frame] = pitch


def place_rest(track: list[int], start: int, length: int) -> None:
    end = min(FRAMES, start + length)
    for frame in range(start, end):
        track[frame] = 0


def write_sequence(track: list[int], start: int, sequence: list[tuple[str, int]]) -> int:
    pos = start
    for name, units in sequence:
        length = units * EIGHTH
        if name == "R":
            place_rest(track, pos, length)
        else:
            place_note(track, pos, midi(name), max(1, length - 2))
        pos += length
    return pos


def lead_track() -> list[int]:
    lead = [0] * FRAMES

    fanfare = [
        ("G4", 2), ("G4", 2), ("G4", 2),
        ("C5", 8), ("G4", 4), ("F4", 1), ("E4", 1), ("D4", 1),
        ("C5", 8), ("G4", 4), ("F4", 1), ("E4", 1), ("D4", 1),
        ("C5", 8), ("G4", 4), ("F4", 1), ("E4", 1), ("F4", 1),
        ("D4", 6), ("R", 2),
    ]
    answer = [
        ("G4", 2), ("G4", 2), ("G4", 2),
        ("C5", 6), ("G4", 3), ("F4", 1), ("E4", 1), ("D4", 1),
        ("C5", 6), ("G4", 3), ("F4", 1), ("E4", 1), ("D4", 1),
        ("C5", 6), ("G4", 3), ("F4", 1), ("E4", 1), ("F4", 1),
        ("D4", 4), ("G4", 2), ("C5", 6), ("R", 2),
    ]

    pos = 0
    pos = write_sequence(lead, pos, fanfare)
    pos = write_sequence(lead, pos, answer)

    coda = [
        ("C5", 3), ("D5", 1), ("E5", 2), ("F5", 2),
        ("G5", 4), ("F5", 2), ("E5", 2), ("D5", 2),
        ("C5", 8), ("R", 4),
    ]
    write_sequence(lead, pos, coda)
    return lead


def harmony_track() -> list[int]:
    harmony = [0] * FRAMES
    chords = [
        "C4", "C4", "F3", "G3",
        "C4", "F3", "G3", "C4",
        "C4", "C4", "F3", "G3",
        "C4", "F3", "G3", "C4",
        "F3", "G3", "C4", "C4",
    ]
    pos = 0
    for chord in chords:
        root = midi(chord)
        for beat in range(4):
            start = pos + beat * QUARTER
            if start >= FRAMES:
                break
            place_note(harmony, start, root, QUARTER - 1)
        pos += BAR
    return harmony


def bass_track() -> list[int]:
    bass = [0] * FRAMES
    roots = [
        "C2", "G2", "F2", "G2",
        "C2", "F2", "G2", "C2",
        "C2", "G2", "F2", "G2",
        "C2", "F2", "G2", "C2",
        "F2", "G2", "C2", "C2",
    ]
    pos = 0
    for root_name in roots:
        root = midi(root_name)
        fifth = root + 7
        octave = root + 12
        pattern = [root, root, fifth, octave]
        for beat, pitch in enumerate(pattern):
            start = pos + beat * QUARTER
            if start >= FRAMES:
                break
            place_note(bass, start, pitch, 14)
            if start + EIGHTH < FRAMES:
                place_note(bass, start + EIGHTH, root, 8)
        pos += BAR
    return bass


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = bytes(lead_track() + harmony_track() + bass_track())
    if len(data) != FRAMES * 3:
        raise AssertionError(f"expected {FRAMES * 3} bytes, got {len(data)}")
    OUT.write_bytes(data)
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
