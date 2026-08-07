SIXIES C64 FONT ASM PACK

Files:
- SixiesFont.asm
  35 glyphs, A-Z and 1-9, 8 bytes per glyph.
  Generic .byte syntax suitable for KickAssembler and easy to adapt.

- SixiesFont_charset.bin
  Full 2048-byte C64 character set.
  A-Z are placed at codes $41-$5A.
  1-9 are placed at codes $31-$39.
  All other character slots are blank.

- SixiesFont_indices.asm
  Constants for compact A-Z / 1-9 glyph indexing.

- SixiesFont_example.asm
  KickAssembler example showing how to install the charset at $2000.

Font format:
- 8x8 pixels
- 1 bit per pixel
- 8 bytes per glyph
- bit 7 = leftmost pixel
- bit 0 = rightmost pixel
