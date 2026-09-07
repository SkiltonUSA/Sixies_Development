# Atari port architecture and research

## Target and high-resolution choice

The baseline is an NTSC Atari 800XL with 64K. The enhanced profile is a
130XE with 128K. Both execute the same 6502 XEX and preserve the OS for keyboard,
clock, and disk services.
The display also works on PAL, but durations currently use 60 Hz frame counts
and the SID player uses a 50-to-60 Hz conversion. PAL-specific pacing remains
future work; use the supplied NTSC launcher for the intended timing.

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
| `$0082-$0098` | Private zero-page pointers, counters, and unbanked PORTB state |
| `$2000` to before `$3000` | Bank-safe CODE: main controller, rules, core renderer and copy routines |
| `$3000-$30C9` | 1K-aligned ANTIC display list |
| `$30CA` to before `$8000` | RODATA assets/tables, LOGIC code, then BSS state; exact ends in `build/sixies.map` |
| `$8000-$8F9F` | First 100 bitmap rows |
| `$8FA0-$8FFF` | Padding required before the next 4K ANTIC fetch region |
| `$9000-$9E5F` | Final 92 bitmap rows |
| `$9E60-$9F4F` | Non-displayed temporary callout underlay |
| `$A000` to before `$C000` | AUXCODE, SID music code/stream, font, alternate display list and page-aligned music buffers; BASIC must be off |
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
grid are stored in lossless PackBits/backreference streams. One shared 6502 routine expands
them directly across the 31 reserved framebuffer pages, including ANTIC's
`$8FA0-$8FFF` boundary gap. Literal packets are `$00-$7F` (length minus one);
repeat packets are `$81-$FF`. The previously unused `$80` marker is followed by
a byte distance and byte length, both 1..255. Overlapping backward copies reuse
nearby scanlines without changing any source pixel. Host round trips and tests
of the compiled 6502 decoder verify the complete framebuffer. Only trusted
build-generated streams are accepted by the compact runtime decoder.

Link-time assertions keep CODE below the bank window, BSS below the screen,
the display list aligned, the overlay below high RAM and music buffers below
OS ROM. MAIN/HIRAM linker regions reject overflow. Inspect `build/sixies.map`
after every asset/code change rather than relying on historical free-byte counts.

## Routine ownership and timing

| Module / entry point | Contract |
| --- | --- |
| `rules.s`: `placement_valid` | Reads cursor/orientation/board; carry indicates valid; computes active/partner indices without changing board |
| `rules.s`: `resolve_at` | A is origin; commits groups/chains and 16-bit score; creation/clear bonuses (+25/+50/+100) precede the placement-wide ×1, ×2, ×3… multiplier |
| `rules.s`: `measure_board_pressure` | One 25-cell scan computes occupied count, four count, and temporary four eligibility before each deal |
| `rules.s`: `spawn_piece` | Applies density rescue first, then 75/25 normal generation; useful singles use empty-neighbor weights and fall back safely |
| `effects.s`: `present_merge` | Owns shake/ripple/firework/award/chain-badge/callout sequence; preserves board/origin/partner/value, reuses finished group queue and renderer scratch |
| `graphics.s`: `draw_piece_sidebar` | Mirrors the hovering pair's right/down/left/up orientation and die order in the next-piece panel |
| `main.s`: `poll_action` | Nonblocking ACTION or NONE; preserves X/Y, clobbers A/flags and `zp_temp`; joystick fire state distinguishes pending placement from consumed rotation |
| `main.s`: `service_animation_input` | Saves shared input scratch; retains one movement/rotation, discards placement, applies mute/reduced-flashing settings without drawing |
| `graphics.s`: `wait_frames` | Cooperative frame wait; services audio and animation input each OS tick; owns `zp_frames/zp_old_frame` |
| `sound.s`: `sound_update` | Idempotent within an RTCLOK tick; effect envelopes preserve X/Y; title-music decoding may clobber them |
| `credits.s`: attract timer | Polls every foreground iteration; reveals music credits when the two-second countdown expires; no blocking reveal wait |
| `ui.s` | High-score save status and post-score retry input; not called from interrupts or within callout underlay holds |
| `high_scores.s`: save | Carry clear on successful SIO; always retains RAM table, sets saved/session-only status for the UI |

Animations are cooperative, not interrupt-driven: movement takes effect after
the current placement finishes resolving. No second placement can re-enter
rules during a chain. All drawing stays in foreground code, avoiding shared
scratch corruption and half-restored overlays from a re-entrant VBI renderer.
The award appears below the permanent left-sidebar score for 18 frames. Chain
merges then shoot a two-character multiplier badge diagonally through five positions before the
official callout remains visible for 30 frames. The supplied 80×32 chain banner
occupies the otherwise blank right sidebar at rows 120–151 for the same chain
presentation, then its input-loop timer leaves it visible for one more second
without blocking movement, placement, or audio. The other three opaque overlays share
one bounded `$9E60` underlay buffer and restore the exact width/height they save;
they never overlap in time. Reduced flashing skips the spiral, ripples, star
pulses and full-screen inversion, but retains score and multiplier feedback; an
in-flight XOR is always paired with restoration. Future shorter/overlapping
animations must preserve this underlay ownership and the player's reading time.

The new-game controller temporarily clears `piece_visible` before the initial
render, runs the clockwise 25-cell spiral through its restored center frame,
then enables and dirty-draws the hovering piece. The sidebar preview does not
depend on `piece_visible`, so it remains visible during the opening effect.

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

## Verification and remaining work

`make test` builds the boot disk before running integration tests. CPU-level
py65 tests execute the linked XEX for probabilities, chains, pair resolution,
boundaries, forced singles, high-score insertion/save failures, input chords,
audio tick wrap, credit reveal timing and exact overlay restoration. The disk
packager preserves sector 720; CI installs pinned Pillow/py65 and disk tools
and publishes XEX plus ATR artifacts without requiring a ROM.

The period-to-Game-Over shortcut is compiled only into `make debug`'s separate
binary. `build/previews/runtime-game.png` and `runtime-confirm.png` are rendered
by executing actual assembly, not separately drawn UI mockups.

Remaining validation: real display/POKEY timing on both machines, long
unattended attract cycling, write-protected disk retry, and PAL-specific rate
handling. CPU tests do not emulate ANTIC raster effects or certify no flicker.
Potential later enhancements include PMG overlays, specialized blitters, a
130XE back buffer and an independent randomized rule oracle. Keep them separate
from this stability pass; do not replace detailed monochrome masters merely
to gain memory or change Apple scoring/group-resolution rules to simplify
code. The 75% pair rate and milestone-unlocked Atari deal pool are intentional
gameplay design differences and are covered by compiled-code tests.

## Reference implementations reviewed

- [Atari Assembly Language Programmer's Guide, display-list chapter](https://www.atariarchives.org/alp/chapter_4.php)
- [AtariAge: writing assembly programs that boot from disk](https://forums.atariage.com/topic/241044-writing-asm-programs-that-boot-from-disk/)
- [AtariAge: current Atari 800XL/XE assembly tool discussion](https://forums.atariage.com/topic/350850-assembly-atari-800xlxe/)
- [Blue Max](https://github.com/sarnau/Atari-BlueMax), [Fort Apocalypse](https://github.com/heyigor/FortApocalypse), and [Pharaoh's Curse](https://github.com/sarnau/Atari-PharaohsCurse) for complete reverse-engineered game layouts
- [dialtr/atari-8tbit](https://github.com/dialtr/atari-8tbit) and [Floppy-Bord](https://github.com/codingbychanche/Floppy-Bord) for small build/disk examples
- [cc65 extended Atari headers](https://github.com/billkendrick/cc65_atar8bit_extended_headers) for OS/hardware naming patterns
- [MADS](https://github.com/tebe6502/Mad-Assembler) and [ZX0](https://github.com/einar-saukas/ZX0) as evaluated alternate assembler/compressor tools
