#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
OUT = BUILD / "StarwarsScrollerDemo.sls"


def main() -> None:
    BUILD.mkdir(exist_ok=True)
    prg = BUILD / "StarwarsScrollerDemo-sparkle-part.prg"

    if not prg.exists():
        raise SystemExit("build/StarwarsScrollerDemo-sparkle-part.prg is missing; run scripts/build.sh first")

    lines = [
        "[Sparkle Loader Script]",
        "Path:\tStarwarsScrollerDemo-sparkle.d64",
        "Header:\tstarwars demo",
        "ID:\tc64u",
        "Name:\tStarwars Demo",
        "Start:\t080d",
        "File:\tStarwarsScrollerDemo-sparkle-part.prg",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Built {OUT}")


if __name__ == "__main__":
    main()
