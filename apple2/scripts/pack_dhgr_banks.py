#!/usr/bin/env python3
"""RLE-pack existing 8 KB auxiliary and main DHGR banks."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
GENERATOR_SPEC = importlib.util.spec_from_file_location(
    "generate_presents", SCRIPT_DIR / "generate_presents.py"
)
assert GENERATOR_SPEC is not None and GENERATOR_SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(GENERATOR_SPEC)
GENERATOR_SPEC.loader.exec_module(GENERATOR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aux", required=True, type=Path)
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--header", required=True, type=Path)
    parser.add_argument("--prefix", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    auxiliary_page = args.aux.read_bytes()
    main_page = args.main.read_bytes()
    if len(auxiliary_page) != GENERATOR.A2FM.PAGE_BYTES:
        raise ValueError("auxiliary DHGR bank must be exactly 8192 bytes")
    if len(main_page) != GENERATOR.A2FM.PAGE_BYTES:
        raise ValueError("main DHGR bank must be exactly 8192 bytes")
    GENERATOR.write_packed_screen(
        main_page,
        auxiliary_page,
        args.output,
        args.header,
        None,
        args.prefix.upper(),
    )


if __name__ == "__main__":
    main()
