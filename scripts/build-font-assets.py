#!/usr/bin/env python3

import pathlib
import re
import sys


BYTE_PATTERN = re.compile(r"\$([0-9a-fA-F]{2})")
GAME_OVER_TEXT = "GAME OVER"
GAME_OVER_PROMPT = "PRESS N FOR NEW GAME"


def read_glyphs(path):
    glyphs = {}
    name = None
    for raw_line in path.read_text(encoding="ascii").splitlines():
        line = raw_line.strip()
        if line.startswith("// "):
            candidate = line[3:].strip()
            name = candidate if len(candidate) == 1 and candidate.isalnum() else None
            continue
        if name and line.startswith(".byte"):
            values = bytes(int(value, 16) for value in BYTE_PATTERN.findall(line))
            if len(values) != 8:
                raise ValueError(f"glyph {name} must contain exactly 8 bytes")
            glyphs[name] = values
            name = None
    expected = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    if set(glyphs) != expected:
        raise ValueError("font source must contain A-Z and 0-9")
    return glyphs


def format_bytes(values):
    return ",".join(f"${value:02x}" for value in values)


def scaled_digit(glyph):
    rows = []
    for source_row in glyph:
        expanded = 0
        for bit in range(7, -1, -1):
            expanded = (expanded << 2) | (3 if source_row & (1 << bit) else 0)
        rows.extend((expanded, expanded))
    top = rows[:8]
    bottom = rows[8:]
    return bytes(
        [row >> 8 for row in top]
        + [row & 0xff for row in top]
        + [row >> 8 for row in bottom]
        + [row & 0xff for row in bottom]
    )


def write_game_over(glyphs, output):
    lines = [
        "; Generated from src/assets/font/SixiesFont_image.asm.",
        "; Nine source glyphs expanded into the large multicolor end banner.",
        "* = $5f80",
        "GameOverLabel:",
    ]
    for character in GAME_OVER_TEXT:
        lines.append(f"; {character if character != ' ' else 'space'}")
        values = bytes(8) if character == " " else glyphs[character]
        lines.append(f"!byte {format_bytes(values)}")
    lines.extend((
        "",
        "; Expands one four-bit font nibble into four multicolor pixels.",
        "GameOverMulticolorExpand:",
        "!byte $00,$03,$0c,$0f,$30,$33,$3c,$3f",
        "!byte $c0,$c3,$cc,$cf,$f0,$f3,$fc,$ff",
    ))
    output.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_game_over_prompt(output):
    lines = [
        "; Generated from src/assets/font/SixiesFont_image.asm.",
        "; Full-width end-screen prompt rendered with the default Sixies font.",
        "* = $4ad0",
        'GameOverPromptText: !text "PRESS N FOR NEW GAME"',
    ]
    lines.extend((
        "",
        "DrawGameOverPrompt:",
        "    lda #<GameOverPromptText",
        "    ldx #>GameOverPromptText",
        "    jsr SetHighScoreTextSource",
        "    lda #20",
        "    sta highTextLength",
        "    lda #23",
        "    sta highTextRow",
        "    lda #0",
        "    sta highTextColumn",
        "    lda #COLOR_WHITE",
        "    sta highTextColor",
        "    jmp DrawSixiesMulticolorText",
    ))
    output.write_text("\n".join(lines) + "\n", encoding="ascii")


def write_large_digits(glyphs, output, digit_data=None):
    lines = [
        "; Generated from src/assets/font/SixiesFont_image.asm.",
        "; Ten 16x16 score glyphs in VIC-II character order.",
        "* = $5e40",
        "LargeDigitFont:",
    ]
    for index, digit in enumerate("0123456789"):
        if digit_data is None:
            scaled = scaled_digit(glyphs[digit])
        else:
            scaled = digit_data[index * 32:(index + 1) * 32]
        lines.extend((
            f"; {digit}",
            f"!byte {format_bytes(scaled[:16])}",
            f"!byte {format_bytes(scaled[16:])}",
        ))
    output.write_text("\n".join(lines) + "\n", encoding="ascii")


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit("usage: build-font-assets.py SixiesFont.asm OUTPUT_DIRECTORY [SixiesDigits16.bin]")
    source = pathlib.Path(sys.argv[1])
    output = pathlib.Path(sys.argv[2])
    glyphs = read_glyphs(source)
    digit_data = pathlib.Path(sys.argv[3]).read_bytes() if len(sys.argv) == 4 else None
    if digit_data is not None and len(digit_data) != 320:
        raise ValueError("16x16 digit data must contain exactly 320 bytes")
    write_game_over(glyphs, output / "game_over.asm")
    write_game_over_prompt(output / "game_over_prompt.asm")
    write_large_digits(glyphs, output / "large_digits.asm", digit_data)
    print("Generated GAME OVER and 16x16 score glyphs from 36 image-extracted glyphs")


if __name__ == "__main__":
    main()
