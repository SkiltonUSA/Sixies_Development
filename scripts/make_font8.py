#!/usr/bin/env python3
"""Build the raw 8x8 border-scroller font (parallax_font8.bin, glyphs $00-$3f).
Source: a charset as KickAssembler .byte text (first 64 glyphs used),
or the VICE chargen ROM if no text file is given.

NOTE: the committed parallax_font8.bin is a custom chunky font whose .txt
source is not in the repo. Running this with no argument replaces it with
the plain ROM font - only do that deliberately."""
import re, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else None
if SRC and SRC.endswith('.txt'):
    data = bytearray()
    for line in open(SRC):
        if '.byte' not in line: continue
        for h in re.findall(r'\$([0-9a-fA-F]{2})', line):
            data.append(int(h, 16))
    font = bytes(data[:512])            # glyphs $00-$3f
else:
    rom = open(SRC or '/Applications/vice-arm64-sdl2-3.9/VICE.app/Contents/Resources/share/vice/C64/chargen-906143-02.bin','rb').read()
    font = rom[:512]
assert len(font) == 512, len(font)

open('src/assets/parallax_font8.bin','wb').write(font)
print('wrote src/assets/parallax_font8.bin from', SRC or 'chargen ROM')

# preview 'A' (glyph $01)
print("preview 'A':")
for d in range(8):
    r = font[8+d]
    print(''.join('#' if r & (1<<(7-i)) else '.' for i in range(8)))
