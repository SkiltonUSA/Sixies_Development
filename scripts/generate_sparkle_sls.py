#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
OUT = BUILD / "bangalore.sls"


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    prg = BUILD / "bangalore-sparkle-part.prg"

    if not prg.exists():
        raise SystemExit("build/bangalore-sparkle-part.prg is missing; run scripts/build.sh first")

    lines = [
        "[Sparkle Loader Script]",
        "Path:\tbangalore-sparkle.d64",
        "Header:\tstarwar demo",
        "ID:\tc64u",
        "Name:\tStarwar Demo",
        "Start:\t080d",
        "File:\tbangalore-sparkle-part.prg",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Built {OUT}")


if __name__ == "__main__":
    main()
