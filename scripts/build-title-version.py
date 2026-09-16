#!/usr/bin/env python3

"""Advance and render the workspace build revision into a C64 intro sprite."""

import argparse
import pathlib


SPRITE_BYTES = 64
BASE_PROMPT_BYTES = 5 * SPRITE_BYTES
MAX_REVISION = 999

# Three columns by seven rows. Six glyphs plus one blank column between each
# fit one 24-pixel-wide hi-res sprite: V1.xxx.
GLYPHS = {
    "V": ("101", "101", "101", "101", "101", "101", "010"),
    ".": ("000", "000", "000", "000", "000", "010", "010"),
    "0": ("111", "101", "101", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "010", "010", "111"),
    "2": ("110", "001", "001", "010", "100", "100", "111"),
    "3": ("110", "001", "001", "010", "001", "001", "110"),
    "4": ("101", "101", "101", "111", "001", "001", "001"),
    "5": ("111", "100", "100", "110", "001", "001", "110"),
    "6": ("011", "100", "100", "110", "101", "101", "010"),
    "7": ("111", "001", "010", "010", "100", "100", "100"),
    "8": ("010", "101", "101", "010", "101", "101", "010"),
    "9": ("010", "101", "101", "011", "001", "001", "110"),
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, type=pathlib.Path)
    parser.add_argument("--base-prompt", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--version-text", required=True, type=pathlib.Path)
    return parser.parse_args()


def next_revision(state_path):
    revision = 0
    if state_path.exists():
        raw = state_path.read_text(encoding="ascii").strip()
        if raw:
            revision = int(raw)
        if not 0 <= revision <= MAX_REVISION:
            raise ValueError(f"invalid build revision in {state_path}: {raw!r}")
    revision = revision % MAX_REVISION + 1
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(f"{revision}\n", encoding="ascii")
    return revision


def build_version_sprite(label):
    if len(label) != 6:
        raise ValueError(f"version label must contain six characters: {label!r}")
    rows = []
    for row in range(7):
        bits = "0".join(GLYPHS[character][row] for character in label) + "0"
        if len(bits) != 24:
            raise AssertionError(f"version row is {len(bits)} pixels, expected 24")
        rows.extend(int(bits[offset:offset + 8], 2) for offset in range(0, 24, 8))
    rows.extend(bytes((21 - 7) * 3))
    rows.append(0)
    if len(rows) != SPRITE_BYTES:
        raise AssertionError(f"version sprite is {len(rows)} bytes")
    return bytes(rows)


def main():
    args = parse_args()
    base_prompt = args.base_prompt.read_bytes()
    if len(base_prompt) != BASE_PROMPT_BYTES:
        raise ValueError(
            f"{args.base_prompt} must contain five sprites "
            f"({BASE_PROMPT_BYTES} bytes), got {len(base_prompt)}"
        )

    revision = next_revision(args.state)
    label = f"V1.{revision:03d}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build_version_sprite(label) + base_prompt)
    args.version_text.parent.mkdir(parents=True, exist_ok=True)
    args.version_text.write_text(f"{label}\n", encoding="ascii")
    print(f"Built title sprites for {label}")


if __name__ == "__main__":
    main()
