# Shiru NES Screen Tool reference

Sixies uses the data formats and RLE behavior documented by Shiru's NES Screen
Tool (NESst) as an interoperability reference.

- Author: Shiru
- Version reviewed: 2.51, dated 2020-02-24
- Official page: https://shiru.untergrund.net/software.shtml
- Official archive: https://shiru.untergrund.net/files/nesst.zip
- Local archive README SHA-256:
  `459ddbbcb08e05bcc0d053b299132c81e7caf702872d3f3141d143cdc2446df4`
- Local `UnitMain.cpp` SHA-256:
  `059b18890b13a051ffb0afb4d7166f7b7832501b2650335244e27f4121351730`

The upstream README releases the program and source code into the public
domain. The original NESASM RLE decoder is retained here with line endings
normalized to LF. The Windows executable and Borland VCL user-interface source
are not required by the Sixies build. Portable, bounds-checked implementations
of the relevant formats live in `scripts/nes_graphics.py`.

Supported compatibility behavior:

- 960-byte and 1024-byte standard `.nam` screens
- 64-byte NES background attribute tables
- 16-byte `.pal` background palette sets
- NESst tag-and-repeat `.rle` streams
- Raw `.chr` and iNES CHR-ROM inspection

Metasprite banks and variable-size `.map` files are documented upstream but
are deferred until Sixies needs sprite animation or scrolling maps.
