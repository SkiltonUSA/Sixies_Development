#!/usr/bin/env python3
"""Reduce a Basic Pitch MIDI transcription to three PAL SID voice tracks."""

from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import pretty_midi


FPS = 50
FRAMES = 40 * FPS
PITCHES = 128


def strength_matrix(midi_path: Path) -> np.ndarray:
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    strength = np.zeros((FRAMES, PITCHES), dtype=np.float32)
    for instrument in midi.instruments:
        for note in instrument.notes:
            start = max(0, min(FRAMES - 1, round(note.start * FPS)))
            end = max(start + 1, min(FRAMES, round(note.end * FPS)))
            strength[start:end, note.pitch] = np.maximum(
                strength[start:end, note.pitch], note.velocity
            )
    return strength


def monophonic_path(
    strength: np.ndarray,
    low_pitch: int,
    high_pitch: int,
    rest_score: float,
    low_pitch_bias: float,
) -> np.ndarray:
    pitches = np.array([-1, *range(low_pitch, high_pitch + 1)])
    state_count = len(pitches)
    transition = np.empty((state_count, state_count), dtype=np.float32)

    for old_index, old_pitch in enumerate(pitches):
        for new_index, new_pitch in enumerate(pitches):
            if old_pitch < 0 and new_pitch < 0:
                cost = 0
            elif old_pitch < 0:
                cost = 10
            elif new_pitch < 0:
                cost = 4
            elif old_pitch == new_pitch:
                cost = -5
            else:
                cost = 7 + 0.55 * abs(old_pitch - new_pitch)
            transition[old_index, new_index] = cost

    emission = np.full((FRAMES, state_count), -1000, dtype=np.float32)
    emission[:, 0] = rest_score
    for state, pitch in enumerate(pitches[1:], 1):
        values = strength[:, pitch].copy()
        values[values == 0] = -1000
        values[values > 0] += low_pitch_bias * (high_pitch - pitch)
        emission[:, state] = values

    scores = np.full((FRAMES, state_count), -1e9, dtype=np.float32)
    previous = np.zeros((FRAMES, state_count), dtype=np.int16)
    scores[0] = emission[0]
    for frame in range(1, FRAMES):
        candidates = scores[frame - 1, :, None] - transition
        previous[frame] = np.argmax(candidates, axis=0)
        scores[frame] = (
            candidates[previous[frame], np.arange(state_count)] + emission[frame]
        )

    result = np.empty(FRAMES, dtype=np.int16)
    state = int(np.argmax(scores[-1]))
    for frame in range(FRAMES - 1, -1, -1):
        result[frame] = pitches[state]
        state = previous[frame, state]
    return result


def remove_selected(
    strength: np.ndarray, selected: np.ndarray, suppress_octave: bool = False
) -> np.ndarray:
    remaining = strength.copy()
    for frame, pitch in enumerate(selected):
        if pitch < 0:
            continue
        remaining[frame, pitch] = 0
        if suppress_octave and pitch >= 12:
            remaining[frame, pitch - 12] *= 0.45
    return remaining


def encode_voice(path: np.ndarray) -> bytes:
    encoded = bytearray(FRAMES)
    previous = -1
    for frame, pitch in enumerate(path):
        if pitch < 0:
            encoded[frame] = 0
        elif pitch != previous:
            encoded[frame] = int(pitch) | 0x80
        else:
            encoded[frame] = int(pitch)
        previous = int(pitch)
    return bytes(encoded)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("midi", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    strength = strength_matrix(args.midi)
    lead = monophonic_path(strength, 57, 95, 24, 0.05)
    remaining = remove_selected(strength, lead, suppress_octave=True)
    harmony = monophonic_path(remaining, 45, 84, 23, 0.03)
    remaining = remove_selected(remaining, harmony)
    bass = monophonic_path(remaining, 28, 57, 20, 0.15)

    args.output.write_bytes(
        encode_voice(lead) + encode_voice(harmony) + encode_voice(bass)
    )
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
