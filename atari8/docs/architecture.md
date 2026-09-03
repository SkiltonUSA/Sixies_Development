# Atari port architecture and research

## Target and high-resolution choice

The baseline is an NTSC or PAL Atari 800XL with 64K. The enhanced profile is a
130XE with 128K. Both execute the same 6502 XEX and preserve the OS for keyboard,
clock, and disk services.

| Display option | Effective picture | Advantages | Cost / decision |
| --- | --- | --- | --- |
| ANTIC F / GRAPHICS 8 | 320x192, 1bpp | Sharpest standard bitmap; portable one-color pixels; close to C64 hi-res and Apple DHGR | Selected; roughly 7.5K plus a display list; gold header/footer and cyan grid area during gameplay |
| NTSC artifact color in mode F | 320x192 source | Can synthesize extra colors | Phase-, monitor-, and emulator-dependent; poor PAL consistency |
| ANTIC 4/5 character modes | 160/80-pixel color cells | Low RAM, character animation, four colors per line | Less horizontal detail; art would need a second conversion |
| GTIA 9/10/11 | 80x192 with 9/16 shades or hues | Strong color/gradient effects | Too coarse for a readable 5x5 board and small dice |
| Interlaced display lists | Up to 320x384 perceived | Higher vertical detail | Flicker, timing complexity, and capture/display variability |

Player/missile graphics and display-list interrupts remain good future options
for a colored cursor, star particles, and per-region accent colors without
giving up the stable one-bit bitmap.

## Memory and runtime

| Address | Use |
| --- | --- |
| `$0082-$0092` | Private zero-page pointers, counters, and unbanked PORTB state |
| `$2000-$2FDE` | Game and renderer code |
| `$3000-$30C9` | 1K-aligned ANTIC display list |
| `$30CA-$7D29` | Packed assets and lookup tables |
| `$7D2A-$7EDB` | Auxiliary animation, palette flash, and callout save/restore code |
| `$7EDC-$7F6C` | Rule and renderer state |
| `$8000-$8F9F` | First 100 bitmap rows |
| `$8FA0-$8FFF` | Padding required before the next 4K ANTIC fetch region |
| `$9000-$9E5F` | Final 92 bitmap rows |
| `$9E60-$9F4F` | Non-displayed temporary callout underlay |
| `$4000-$7FFF`, extended bank 2 | 130XE cached title framebuffer while selected |

The 130XE probe writes different signatures into two extended banks and restores
the original main-window bytes and PORTB value. All restoration state and the
detected-size flag stay in zero page because `$4000-$7FFF` vanishes from the CPU
view during a bank switch. The bank-copy routines themselves are linked below
`$4000`; the bank is restored before any high-memory game state is accessed.

The current 128K enhancement makes title returns immediate and proves a safe
banking path. A larger second stage can use separate banks for a back buffer,
animation frames, music patterns, and expanded presentation without penalizing
the 64K game.

Title, presentation, instructions, Game Over, and the Apple-derived gameplay
grid are stored in PackBits-style RLE streams. One shared 6502 routine expands
them directly across the 31 reserved framebuffer pages, including ANTIC's
`$8FA0-$8FFF` boundary gap. The grid brings the 64K build close to its fixed
framebuffer boundary, with 147 bytes currently free below `$8000`; future large
assets should use 130XE banks or load from disk.

## Boot and build strategy

`ca65` produces relocatable objects and `ld65` uses `cfg/sixies.cfg` to emit an
Atari segmented executable with a RUN vector at `$02E0`. This keeps source,
labels, map, and listing files friendly to modern debugging while still creating
a normal XEX. Exomizer `sfx 8192 -t168` produces the release executable.
AtariSIO's `dir2atr` wraps it in a standard-density PicoBoot406 ATR, avoiding a
custom sector loader in the first implementation.

The bootable-disk research supports this staged approach: the Atari OS can load
boot sectors directly, while a conventional XEX plus a small boot loader is
easier to develop and remains compatible with DOS and modern emulators. A custom
multi-stage loader becomes useful only when disk streaming or load-time effects
justify its maintenance cost.

## Prioritized assembly improvements

1. **Split common and banked regions.** Enforce a linker segment below `$4000`
   for every routine and datum touched while extended RAM is selected, then put
   immutable art in explicit banks. Add a link-time assertion for the boundary.
2. **Continue specializing dirty rendering.** Cursor movement, rotation,
   placement, merge groups, score digits, and the piece sidebar now update only
   their affected regions. Keep full-screen RLE expansion limited to screen
   transitions, and specialize any future animated overlays the same way.
3. **Use PMG for transient effects.** A player can become the cursor/invalid
   marker and missiles can render stars, freeing the bitmap renderer from many
   OR blits and enabling color.
4. **Page-align and specialize blitters.** Dice are fixed at 4x24 bytes. An
   unrolled copy/erase pair with page-aligned sources is smaller and faster than
   the generic pointer-based OR loop during frequent cell updates.
5. **Move timing into a VBI service.** Queue POKEY envelopes, cursor flashing,
   callout duration, and animation state in a deferred VBI instead of waiting in
   foreground loops. Keep PORTB changes out of interrupt-visible windows.
6. **Add a 128K back buffer.** Render large transitions into an extended bank,
   then copy during blanking. This is a useful enhancement rather than a
   requirement for gameplay.
7. **Create a host rule oracle.** Mirror the 25-byte board and deterministic RNG
   in tests, feed recorded placements to both the model and an emulator build,
   and compare board/score checkpoints. Current tests verify contracts and
   tables but not thousands of generated game sequences.
8. **Add persistent scores through CIO.** Store the Apple-compatible ten-entry
   table as a separate ATR file, with a write-protect/error path and an in-memory
   fallback.
9. **Benchmark compression by asset class.** The runtime PackBits decoder now
   handles sparse full-screen art and Exomizer compresses the complete XEX.
   ZX0 remains worth measuring for denser independently loaded art blocks.
10. **Keep ca65 as the canonical build, evaluate MADS for experiments.** MADS is
    attractive for Atari-specific macros, relocatable blocks, and examples in
    the community, but a toolchain migration would not itself improve runtime
    code. Port proven macros back or add a reproducible alternate target.

## Reference implementations reviewed

- [Atari Assembly Language Programmer's Guide, display-list chapter](https://www.atariarchives.org/alp/chapter_4.php)
- [AtariAge: writing assembly programs that boot from disk](https://forums.atariage.com/topic/241044-writing-asm-programs-that-boot-from-disk/)
- [AtariAge: current Atari 800XL/XE assembly tool discussion](https://forums.atariage.com/topic/350850-assembly-atari-800xlxe/)
- [Blue Max](https://github.com/sarnau/Atari-BlueMax), [Fort Apocalypse](https://github.com/heyigor/FortApocalypse), and [Pharaoh's Curse](https://github.com/sarnau/Atari-PharaohsCurse) for complete reverse-engineered game layouts
- [dialtr/atari-8tbit](https://github.com/dialtr/atari-8tbit) and [Floppy-Bord](https://github.com/codingbychanche/Floppy-Bord) for small build/disk examples
- [cc65 extended Atari headers](https://github.com/billkendrick/cc65_atar8bit_extended_headers) for OS/hardware naming patterns
- [MADS](https://github.com/tebe6502/Mad-Assembler) and [ZX0](https://github.com/einar-saukas/ZX0) as evaluated alternate assembler/compressor tools
