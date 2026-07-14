#!/usr/bin/env python3
"""Generate perspective scroller data + unrolled plotter for src/main.a.

Port of the NoBounds/Rivalry Star Wars scroller technique described at
https://c64demo.com/star-wars-scrollers/ (Starwars.cpp in the NoBounds
public release):

- the crawl lives in a hires bitmap; background is 1-bits, ink is 0-bits,
  so glyph contributions combine with AND and $ff means "empty"
- the scrolltext is streamed into 16 cyclic 256-byte column buffers as
  font-row indices (one buffer per 16px source column)
- for every screen line the generator knows which source pixels survive
  the perspective squeeze, and pre-packs each unique 16px font row into a
  FontData table for that exact bit-picking, so the runtime blit is just
  ldy ScrollData+col,x / lda FontData_a,y / and FontData_b,y / sta bitmap
- vertical perspective comes from stepping the source row index by more
  than one per screen line near the horizon (INX repeats in the unrolled
  plotter)
"""

from __future__ import annotations

import os
import random

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "generated")

# --- geometry ---------------------------------------------------------------

NUM_COLS = 16                 # chars per scrolltext line (16px each => 256px)
MAX_WIDTH = NUM_COLS * 16     # flat width of the crawl at the bottom
HEIGHT = 96                   # screen lines of crawl (12 char rows)
TOP_WIDTH = 128               # crawl width at the horizon (2:1 like the article)
Y_START = 80                  # first bitmap line of the crawl (char row 10)
X_CHAR_START = (40 - MAX_WIDTH // 8) // 2  # centre the 256px area
ROWS_PER_TEXT_LINE = 18       # 16 glyph rows + 2 blank rows

# --- 5x7 font, expanded to 16x16 --------------------------------------------
# Row patterns are 5-bit; the whole font therefore uses only ~25 unique 16px
# rows once expanded, which keeps the FontData tables small (Ksubi's trick).

FONT_5X7 = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "10001", "11001", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "00000", "01100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}

SCROLL_LINES = [
    "A LONG TIME AGO",
    "....",
    "",
    "WAIT DOES ANYONE",
    "UNDERSTAND HOW",
    "HARD IT IS TO",
    "BUILD A STARWARS",
    "SCROLLER....",
    "",
    "NEITHER DID I",
    "UNTIL I STARTED",
    "THIS PROJECT.",
    "THANKS TO",
    "RAISTLINGP, OF",
    "RAISTLIN PAPERS,",
    "RTROUGHTON OF",
    "GENESIS PROJECT",
    "FOR THE WRITE UP",
    "AND NOBOUNDS SRC",
    "AS INSPIRATION",
    "....",
    "",
    "THIS IS A REAL",
    "PERSPECTIVE",
    "BIT-PICKED FONTS",
    "CYCLIC BUFFERS",
    "AND UNROLLED",
    "BITMAP PLOTTERS",
    "....",
    "",
    "GREETINGS TO",
    "GENESIS PROJECT",
    "FOR BEING OPEN",
    "TO NEW CODERS,",
    "LINUS AKESSEN",
    "FOR AWESOME",
    "INSIGHTS INTO",
    "C64...",
    "",
    "",
    "YES THE INTRO",
    "IS LAME AND",
    "BORING, BUT",
    "COME ON, ITS A",
    "STARWARS",
    "SCROLLER",
    "",
    "",
    "AND",
    "WHO DOESNT LIKE",
    "A GOOD 8BIT",
    "1MHZ STARWARS",
    "SCROLLER???",
    "",
    "",
    "",
    "GREETINGS TO",
    "ALL OLD",
    "SCHOOLERS",
    "",
    "",
    "PARALAX,",
    "",
    "HELLRAISERS,",
    "",
    "DREAM WARRIORS,",
    "",
    "",
    "",
    "",
    "PINK PANTHER.",
    "",
    "",
]


def expand_glyph(rows5: tuple[str, ...]) -> list[int]:
    """Expand a 5x7 glyph to 16 rows of 16-bit patterns (px 0 and 15 blank)."""
    # column i of the 5px grid covers pixels [1 + floor(2.8*i), 1 + floor(2.8*(i+1)))
    bounds = [1 + (i * 14) // 5 for i in range(6)]
    out = [0] * 16
    for r, row in enumerate(rows5):
        short = 0
        for i, bit in enumerate(row):
            if bit == "1":
                for px in range(bounds[i], bounds[i + 1]):
                    short |= 1 << (15 - px)
        out[1 + 2 * r] = short
        out[2 + 2 * r] = short
    return out


def build_font_and_text():
    used = sorted({ch for line in SCROLL_LINES for ch in line.upper()} | {" "})
    for ch in used:
        assert ch in FONT_5X7, f"no glyph for {ch!r}"
    char_index = {ch: i for i, ch in enumerate(used)}

    glyphs = [expand_glyph(FONT_5X7[ch]) for ch in used]

    shorts = [0]  # index 0 must stay the blank row
    for g in glyphs:
        for s in g:
            if s not in shorts:
                shorts.append(s)
    assert len(shorts) <= 48, f"too many unique font rows: {len(shorts)}"

    remapped = [[shorts.index(glyphs[c][r]) for c in range(len(used))]
                for r in range(16)]

    text_bytes = []
    for line in SCROLL_LINES:
        line = line.upper()[:NUM_COLS]
        pad = (NUM_COLS - len(line)) // 2
        line = (" " * pad + line).ljust(NUM_COLS)
        text_bytes.extend(char_index[ch] for ch in line)
    text_bytes.append(0xFF)
    return used, shorts, remapped, text_bytes


# --- perspective mapping -----------------------------------------------------

def line_width(y: int) -> int:
    w = TOP_WIDTH + (MAX_WIDTH - TOP_WIDTH) * (y + 0.5) / HEIGHT
    return min(MAX_WIDTH, int(round(w / 2)) * 2)  # even, so halves stay integral


def screen_to_source(y: int) -> list[int]:
    """For screen line y, map each of the 256 screen pixels to a source pixel
    (or -1 outside the trapezoid). Same maths as Starwars.cpp."""
    lookup = [-1] * MAX_WIDTH
    half = line_width(y) / 2
    mid = MAX_WIDTH // 2
    for xp in range(int(half)):
        frac = xp / half
        lookup[mid + xp] = int(mid + frac * (mid - 1))
        lookup[mid - 1 - xp] = int((mid - 1) - frac * (mid - 1))
    return lookup


def build_perspective():
    """Per (line, byte): list of (column, pixel_mapping) with <=2 entries."""
    mappings = {}  # cache by (width, byte) since equal widths map identically
    lines = []
    for y in range(HEIGHT):
        lookup = screen_to_source(y)
        key_w = line_width(y)
        row = []
        for xb in range(MAX_WIDTH // 8):
            cache_key = (key_w, xb)
            if cache_key not in mappings:
                per_col = []  # [(col, [src_bit or None]*8)]
                for px in range(8):
                    src = lookup[xb * 8 + px]
                    if src < 0:
                        continue
                    col, bit = src >> 4, src & 15
                    if bit in (0, 15):  # always blank in the font
                        continue
                    entry = next((e for e in per_col if e[0] == col), None)
                    if entry is None:
                        entry = (col, [None] * 8)
                        per_col.append(entry)
                    entry[1][px] = bit
                assert len(per_col) <= 2, "more than 2 chars on one byte"
                mappings[cache_key] = per_col
            row.append(mappings[cache_key])
        lines.append(row)
    return lines


def build_fontdata(lines, shorts):
    """Dedupe (pixel_mapping) into FontData tables of len(shorts) bytes."""
    sets = {}
    order = []
    plot = []  # per line: list of (byte_index, [(col, set_id), ...])
    for row in lines:
        prow = []
        for xb, per_col in enumerate(row):
            if not per_col:
                continue
            entry = []
            for col, mapping in per_col:
                formed = []
                for s in shorts:
                    b = 0xFF
                    for px in range(8):
                        bit = mapping[px]
                        if bit is not None and s & (1 << (15 - bit)):
                            b &= ~(1 << (7 - px)) & 0xFF
                    formed.append(b)
                key = tuple(formed)
                if key not in sets:
                    sets[key] = len(order)
                    order.append(key)
                entry.append((col, sets[key]))
            prow.append((xb, entry))
        plot.append(prow)
    return order, plot


def build_virtual_y():
    """Source rows advance faster near the horizon: step = MAX_WIDTH/width."""
    vy, acc = [], 0.0
    for y in range(HEIGHT):
        vy.append(int(acc))
        acc += MAX_WIDTH / line_width(y)
    return vy


# --- emit --------------------------------------------------------------------

def fmt_bytes(values):
    out = []
    for i in range(0, len(values), 16):
        chunk = ",".join(f"${v & 0xff:02x}" for v in values[i:i + 16])
        out.append(f"    !byte {chunk}")
    return out


def main():
    used, shorts, remapped, text_bytes = build_font_and_text()
    lines = build_perspective()
    order, plot = build_fontdata(lines, shorts)
    vy = build_virtual_y()
    nchars = len(used)

    window = vy[-1] + 2
    assert window < 200, f"source window too tall for cyclic buffers: {window}"

    data = ["; generated by scripts/generate_tables.py -- data tables"]
    data.append(f"NUM_FONT_CHARS = {nchars}")
    data.append(f"SCROLL_WINDOW = {window}")
    data.append(f"ROWS_PER_TEXT_LINE = {ROWS_PER_TEXT_LINE}")
    data.append("")
    data.append("font_row_lo:")
    data.append("    !byte " + ",".join(f"<(remapped_font+{r * nchars})" for r in range(16)))
    data.append("font_row_hi:")
    data.append("    !byte " + ",".join(f">(remapped_font+{r * nchars})" for r in range(16)))
    data.append("remapped_font:")
    for r in range(16):
        data.extend(fmt_bytes(remapped[r]))
    data.append("scroll_text:")
    data.extend(fmt_bytes(text_bytes))
    data.append("")

    # per char row of the screen: colour byte (bg high nybble, ink low nybble)
    crawl_inks = [0x09, 0x09, 0x08, 0x08, 0x08, 0x0A,
                  0x0A, 0x0A, 0x07, 0x07, 0x07, 0x07]
    row_colors = [0x01] * 10 + crawl_inks + [0x0B] * 3
    data.append("screen_row_colors:")
    data.extend(fmt_bytes(row_colors))
    data.append("")

    # Starfield: deterministic pseudo-random 0-bit pixels.  Keep the crawl
    # area clean, but fill the lower screen so the scene does not go empty
    # underneath the perspective scroller.
    rng = random.Random(1977)
    stars = []
    used_star_pixels = set()

    def add_stars(count: int, x_min: int, x_max: int, y_min: int, y_max: int) -> None:
        remaining = count
        attempts = 0
        while remaining and attempts < count * 500:
            attempts += 1
            x = rng.randrange(x_min, x_max)
            yy = rng.randrange(y_min, y_max)
            if Y_START <= yy < Y_START + HEIGHT:
                continue
            key = (x, yy)
            if key in used_star_pixels:
                continue
            used_star_pixels.add(key)
            off = (yy // 8) * 320 + (x // 8) * 8 + (yy & 7)
            stars.append((off, 0xFF ^ (0x80 >> (x & 7))))
            remaining -= 1
        if remaining:
            raise SystemExit("could not place requested stars")

    add_stars(36, 0, 320, 0, 80)       # behind and around the banner
    add_stars(20, 0, 54, 0, 200)       # left of the crawl trapezoid
    add_stars(20, 266, 320, 0, 200)    # right of the crawl trapezoid
    add_stars(72, 0, 320, 176, 200)    # extended bottom field
    data.append(f"STAR_COUNT = {len(stars)}")
    data.append("star_lo:")
    data.extend(fmt_bytes([off & 0xFF for off, _ in stars]))
    data.append("star_hi:")
    data.extend(fmt_bytes([off >> 8 for off, _ in stars]))
    data.append("star_val:")
    data.extend(fmt_bytes([v for _, v in stars]))
    data.append("")

    for idx, formed in enumerate(order):
        data.append(f"fd_{idx}:")
        data.extend(fmt_bytes(list(formed)))

    code = ["; generated by scripts/generate_tables.py -- unrolled plotter"]
    code.append("plotter:")
    code.append("plot_base:")
    code.append("    ldx #$00")
    for y in range(HEIGHT):
        step = vy[y] - vy[y - 1] if y else 0
        code.extend(["    inx"] * step)
        cur_col = None  # Y register is stale after inx
        yy = Y_START + y
        for xb, entry in plot[y]:
            for k, (col, set_id) in enumerate(entry):
                if col != cur_col:
                    code.append(f"    ldy SCROLL_DATA+${col * 0x100:04x},x")
                    cur_col = col
                code.append(f"    {'lda' if k == 0 else 'and'} fd_{set_id},y")
            off = (yy // 8) * 320 + (xb + X_CHAR_START) * 8 + (yy & 7)
            code.append(f"    sta BITMAP+${off:04x}")
    code.append("    rts")

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "sw_data.inc"), "w") as f:
        f.write("\n".join(data) + "\n")
    with open(os.path.join(OUT_DIR, "sw_plot.inc"), "w") as f:
        f.write("\n".join(code) + "\n")

    fd_bytes = len(order) * len(shorts)
    print(f"chars used: {nchars}  unique font rows: {len(shorts)}")
    print(f"fontdata sets: {len(order)} ({fd_bytes} bytes)")
    print(f"plot code lines: {len(code)}  window: {window} rows")


if __name__ == "__main__":
    main()
