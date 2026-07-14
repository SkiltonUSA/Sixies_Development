#!/usr/bin/env python3
"""Compose "Galway Nights", an original Martin Galway style SID arrangement.

The tune is written directly as note/duration patterns (no MIDI stage) and
rendered to the same one-byte-per-frame-per-voice stream format the other
drivers in this repo use: 0 = gate off, bit 7 set = hard-restart frame for a
new note, plain value = MIDI note held with the gate open.

Galway trademarks live partly here and partly in the 6502 driver
(src/music/galway_nights.a):
  * voice 1 -- lead with delayed, blooming vibrato and a swept pulse width
  * voice 2 -- dotted-eighth echo of the lead at a quieter sustain level
  * voice 3 -- bouncy octave bass time-shared with pitch-drop kick and
    noise snare, run through a slowly sweeping low-pass filter
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAMES_BIN = ROOT / "src" / "music" / "galway_nights_frames.bin"
INC_PATH = ROOT / "src" / "generated" / "galway_nights.inc"

FRAMES_PER_16TH = 7          # 50 Hz PAL -> ~107 BPM loader pace
SLOTS_PER_BAR = 16
BAR_FRAMES = SLOTS_PER_BAR * FRAMES_PER_16TH
ECHO_DELAY_FRAMES = 3 * FRAMES_PER_16TH  # dotted-eighth Ocean-loader echo

SNARE_PITCH = 125
KICK_PITCH = 126

NOTE_OFFSETS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name: str) -> int:
    letter = name[0]
    rest = name[1:]
    sharp = rest.startswith("#")
    octave = int(rest[1:] if sharp else rest)
    return 12 * (octave + 1) + NOTE_OFFSETS[letter] + (1 if sharp else 0)


def render_events(events, gap_frames: int) -> bytearray:
    """Render (pitch, sixteenths) events; pitch None is a rest."""
    out = bytearray()
    for pitch, sixteenths in events:
        frames = sixteenths * FRAMES_PER_16TH
        if pitch is None:
            out += bytes(frames)
            continue
        hold = frames - 1 - gap_frames
        out += bytes([pitch | 0x80]) + bytes([pitch] * hold) + bytes(gap_frames)
    return out


# --- Melody: 16 bars in A minor over an Andalusian Am-G-F-E descent.
# --- The hook is one syncopated rhythmic motif (2+1+1+2+2+3+1+4)
# --- restated down the progression, with long turnaround notes that
# --- give the blooming vibrato room to sing.
def bar(*pairs):
    events = [(midi(name), dur) for name, dur in pairs]
    if sum(dur for _, dur in pairs) != SLOTS_PER_BAR:
        raise SystemExit(f"bar does not sum to 16 sixteenths: {pairs}")
    return events


HOOK_AM = bar(("A4", 2), ("C5", 1), ("A4", 1), ("E5", 2), ("C5", 2), ("A5", 3), ("G5", 1), ("E5", 4))
HOOK_G = bar(("G4", 2), ("B4", 1), ("G4", 1), ("D5", 2), ("B4", 2), ("G5", 3), ("F5", 1), ("D5", 4))
HOOK_F = bar(("A4", 2), ("C5", 1), ("A4", 1), ("F5", 2), ("C5", 2), ("A5", 3), ("G5", 1), ("F5", 4))

MELODY_BARS = [
    HOOK_AM,
    HOOK_G,
    HOOK_F,
    bar(("G#4", 2), ("B4", 2), ("E5", 2), ("D5", 2), ("B4", 8)),
    HOOK_AM,
    HOOK_G,
    HOOK_F,
    bar(("E5", 2), ("D5", 2), ("B4", 2), ("G#4", 2), ("E5", 8)),
    bar(("A4", 2), ("A4", 2), ("C5", 2), ("F5", 2), ("E5", 4), ("C5", 2), ("A4", 2)),
    bar(("B4", 2), ("B4", 2), ("D5", 2), ("G5", 2), ("F5", 4), ("D5", 2), ("B4", 2)),
    bar(("C5", 2), ("C5", 2), ("E5", 2), ("A5", 2), ("G5", 4), ("E5", 2), ("C5", 2)),
    bar(("D5", 2), ("C5", 2), ("B4", 2), ("G#4", 2), ("B4", 8)),
    HOOK_AM,
    HOOK_G,
    HOOK_F,
    bar(("A4", 2), ("B4", 2), ("C5", 2), ("B4", 2), ("A4", 8)),
]

# Bass roots per bar: Am G F E | Am G F E | F G Am E | Am G F E
BASS_ROOTS = [midi(n) for n in (
    "A1", "G1", "F1", "E1",
    "A1", "G1", "F1", "E1",
    "F1", "G1", "A1", "E1",
    "A1", "G1", "F1", "E1",
)]
# Drum plan: the first and last statements ride a straight backbeat, the
# B section (bars 9-12) switches to a busier loader pattern with ghost
# snares, and bars 8 and 16 end their half with a long snare roll.
LOADER_BARS = set(range(8, 12))
FILL_BARS = {7, 15}


def bass_bar(root: int, style: str):
    if style == "fill":
        return [
            (KICK_PITCH, 2), (root, 2), (SNARE_PITCH, 2), (root + 12, 2),
            (KICK_PITCH, 2),
        ] + [(SNARE_PITCH, 1)] * 6
    if style == "loader":
        return [
            (KICK_PITCH, 2), (root, 1), (root, 1), (SNARE_PITCH, 2), (root + 12, 2),
            (KICK_PITCH, 1), (SNARE_PITCH, 1), (root, 2),
            (SNARE_PITCH, 1), (SNARE_PITCH, 1), (root + 12, 2),
        ]
    return [
        (KICK_PITCH, 2), (root, 2), (SNARE_PITCH, 2), (root + 12, 2),
        (KICK_PITCH, 2), (root, 2), (SNARE_PITCH, 2), (root + 12, 2),
    ]


def main() -> None:
    lead = bytearray()
    for bar_events in MELODY_BARS:
        lead += render_events(bar_events, gap_frames=0)

    bass = bytearray()
    for index, root in enumerate(BASS_ROOTS):
        if index in FILL_BARS:
            style = "fill"
        elif index in LOADER_BARS:
            style = "loader"
        else:
            style = "straight"
        bass += render_events(bass_bar(root, style), gap_frames=2)

    loop_frames = len(MELODY_BARS) * BAR_FRAMES
    if len(lead) != loop_frames or len(bass) != loop_frames:
        raise SystemExit(
            f"stream length mismatch: lead={len(lead)} bass={len(bass)} "
            f"expected={loop_frames}"
        )

    # The echo voice is the lead stream rotated by a dotted eighth; because
    # the melody loops, the wrap-around echo of the final bar lands under
    # bar one exactly as it does live.
    echo = lead[-ECHO_DELAY_FRAMES:] + lead[:-ECHO_DELAY_FRAMES]

    FRAMES_BIN.write_bytes(lead + echo + bass)
    INC_PATH.parent.mkdir(parents=True, exist_ok=True)
    INC_PATH.write_text(
        "; Generated by scripts/generate_galway_sid.py.\n"
        f"GALWAY_LOOP_FRAMES = {loop_frames}\n",
        encoding="ascii",
    )
    seconds = loop_frames / 50
    bpm = 50 * 60 / (4 * FRAMES_PER_16TH)
    print(f"Wrote {FRAMES_BIN.relative_to(ROOT)} ({loop_frames} frames/voice, "
          f"{seconds:.2f}s loop at {bpm:.0f} BPM)")
    print(f"Wrote {INC_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
