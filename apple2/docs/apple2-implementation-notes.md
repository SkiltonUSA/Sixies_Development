# Apple II Implementation Notes

## HGR and DHGR

- HGR Page 1 occupies `$2000-$3FFF`; Page 2 occupies `$4000-$5FFF`.
- The current executable starts at `$4000`, so Page 2 cannot be used without relocating the program.
- Both modes use the Apple II's interleaved scanline layout. A scanline starts at `((y & 7) << 10) + (((y >> 3) & 7) << 7) + ((y >> 6) * $28)` within its page.
- HGR emits bits 0-6 from left to right. Bit 7 selects a half-dot phase shift for the blue/orange color group.
- Two adjacent lit HGR dots are required for a stable white line. Single-dot lines can acquire composite color fringes.
- DHGR emits a continuous 560-bit scanline from alternating auxiliary and main 7-bit bytes. Repeating four-bit patterns produce its 16 color codes; the color index swaps signal bits 1 and 3, and the two grey codes appear nearly identical on a IIe.
- A DHGR Page 1 screen consumes 8 KB at `$2000` in main RAM and another 8 KB at `$2000` in auxiliary RAM.
- `$C004/$C005` are write-activated RAMWRT switches. Reading them does not select the write bank.
- DHGR requires 80-column mode, so mixed-mode text must be written as alternating auxiliary/main text bytes rather than through the 40-column `conio` path.
- The title uses full-screen monochrome DHGR because composite color fringing makes mixed 80-column footer text difficult to read.
- Palette previews are only nominal. Composite NTSC/PAL, RGB adapters, emulators, and the IIGS can produce materially different colors and edge artifacts.

## Program Structure

- Keep game rules, state, and low-frequency UI code in C.
- Put auxiliary-memory copies, drawing inner loops, and cycle-sensitive routines in 6502 assembly.
- Static DHGR pages are stored as ProDOS files and streamed through a 1 KB main-memory buffer. This keeps the executable clear of video memory and avoids embedding 32 KB of art.
- Gameplay uses the supplied full-screen DHGR page directly. Dice update both auxiliary and main banks inside verified-black 24x24 cell interiors; the surrounding bitmap grid remains untouched.
- Release disks package an Exomizer 3.1.2 Apple II/IIe SFX machine payload at `$080D`. The build validates the cc65 AppleSingle input and Exomizer launcher, then decrunches the result and compares it byte-for-byte with the original `$4000` PRG before accepting it. The native executable remains available for map/debug work, and runtime addresses are unchanged after decompression.

## Title Artwork

- `assets/presents_master.ppm` is converted to the title screen's full-screen 560x192 one-bit DHGR layout and RLE-packed as `PRESENTS.RLE`. The stream fits both banks in the not-yet-used dice buffer; startup expands it in 1 KB chunks to Page 1. The presentation displays for 300 NTSC vertical blanks, the initial title for 600, and subsequent presentation/title/instruction pages for 300 each. Graphics are hidden while loading the next page to avoid a visible bank-by-bank transition.
- `assets/title_dhgr_mono_master.a2fm` is the supplied 16 KB b2d monochrome DHGR title. It is imported without re-quantizing or changing its screen bytes.
- The A2FM layout stores the 8 KB auxiliary page first and the 8 KB main page second. `scripts/import_a2fm_asset.py` verifies every pixel against `assets/title_dhgr_mono_reference.png`; the runtime packages the original bytes as one `TITLE.A2FM` file and streams both banks through one ProDOS open, sharing the grid's loader.
- `scripts/generate_instructions.py` pre-renders the framed 560x192 monochrome instruction page from a deterministic 5x7 pixel font and packages it as `INSTRUCT.RLE`. It describes the Apple II controls and game rules rather than retaining the reference image's C64-specific joystick text.
- The attract loop polls the keyboard once per vertical blank. `Space`, `Return`, or `N` starts from any page; if no start key arrives, the initial title advances to instructions after ten seconds and presentation/title/instruction pages then rotate every five seconds. Pending repeats are drained only after startup exits, before the normal grid assets load.
- To preserve the title's fast raw-bank load, `scripts/pack_dhgr_banks.py` instead reduces the less time-sensitive game-over banks from 16,384 bytes to 5,880 bytes as `GAMEOVER.RLE`. The shared RLE loader expands the intro, instructions, and game-over screen one bank at a time through the existing dice buffer.

## Pre-rendered Grid Prototype

- `assets/game_grid_dhgr_mono_master.a2fm` and its reference PNG preserve the supplied full-screen 560-pixel monochrome layout. `scripts/import_a2fm_grid.py` verifies every source pixel, then clears the old reminder panel interior before packing `GRID.A2FM`.
- The importer creates `build/previews/grid_dhgr.png` and verifies that the exact dynamic rectangle selected inside every cell is black in both banks. The supplied artwork has one-pixel phase differences in its last columns and rows, so those rectangles use generated per-column and per-row origins instead of assuming a perfectly uniform pitch.
- Each column begins at a different DHGR byte phase. Auxiliary/main byte offsets and edge masks are generated from the exact 24x24 cell interiors.
- The importer replaces the noisy source `SCORE`, `TOTAL`, and New Game lettering with pre-rendered opaque monochrome glyphs. The footer renders `[N]EW GAME` to expose its keyboard shortcut. The unused `SETTINGS` label, gear, and surrounding footer box are removed completely. It also clears the baked five-digit value. Runtime digits are XOR-blitted into that well so every grid reload can restore the current total. The right panel has no label: a single current die uses its middle slot, while a pair uses the two nearest centered slots.
- The irregular bitmap separator above the footer controls is cleared from source scanlines 163-165. A compact assembly routine draws a stable two-scanline monochrome divider across signals 10-549 in both DHGR banks immediately after the grid loads.
- Pressing `N` during gameplay XOR-blits `ARE YOU SURE [Y/N]?` into the empty footer from a 110-byte generated mask. `Y` reloads the board; `N` XOR-restores the footer, drains repeat events until the keyboard is quiet for three frames, and resumes the current game unchanged.
- The high-resolution C64 mascot master is aspect-corrected to 88x55 DHGR signals and reduced to monochrome at build time. It replaces the decorative `ROUND/MOVES/NEXT` block beneath the left score while remaining part of the static grid page.
- `GRID.A2FM` is packaged on the ProDOS image. A new game streams its auxiliary and main halves to HGR Page 1; movement, rotation, placement, and merges clear only affected black cell interiors without clearing or procedurally rebuilding the grid.
- The emulator launches with its AppleColor-compatible RGB card enabled. Every DHGR screen selects RGB mode 11 with the standard AN3/80COL sequence, displaying the supplied 560x192 one-bit pages as black and white instead of passing their edges through NTSC artifact-color decoding.

## Dice Artwork

- `assets/die_1_master.png` through `assets/die_6_master.png` preserve the supplied white, blue, green, purple, yellow, and orange dice as conversion masters.
- `scripts/generate_hgr_dice.py` validates the supplied masters and constructs native 48x24 monochrome DHGR signal masks. The 12-signal by 5-scanline rounded pips compensate for DHGR's non-square 560x192 pixels, so values remain legible instead of collapsing into vertical bars. The generator emits paired auxiliary/main planes for all six faces at each of the five board-column phases into the 8.4 KB `DICE.BLITS` file, along with invalid-position marks. The obsolete procedural HGR fallback and its embedded masks are omitted; missing required assets stop on a text error instead of loading the rejected colored fallback grid.
- Runtime dice use monochrome white faces with black pips. Earlier artifact-color patterns were technically valid four-bit DHGR groups but produced severe vertical bands under izapple2's composite display path; monochrome keeps every value stable and readable across composite, RGB, and emulator output. The supplied colored masters remain preserved as source references.
- Player-controlled dice use the same full opaque sprite as committed dice. Separate corner markers were removed because their second outline was visually confused with the die edge.
- Invalid hover positions use a precomputed rounded die silhouette with diagonal hatching instead of an `X`. Each die in a pair is evaluated independently, so only the sprite directly overlapping an occupied cell is hatched; the normal dirty-cell path restores the committed die when the cursor moves away.
- While gameplay waits for input, a VBL-driven 18-frame timer XOR-inverts only the active preview cell interiors. The existing assembly ripple primitive maps auxiliary HGR through `80STORE/PAGE2`, restores Page 1 immediately, and repeats the XOR to recover every underlying pixel exactly. A keypress restores the normal preview before movement, rotation, or placement is processed; the current sidebar dice never flash, and occupied targets keep their per-die hatch rule.
- The right panel reuses the center board-column sprite phase at HGR X 247. Generated offsets and masks prove the auxiliary/main alignment at build time, so current-piece updates require no additional sprite bank or disk access.
- `build/previews/dice_1_6.png` is a deterministic enlarged preview of all six reduced masks. The runtime verifies `DICE.BLITS` with a generated checksum before enabling the DHGR grid renderer.

## Gameplay Rendering Optimization

- Cursor movement builds the union of old and new preview cells, restores each unique 28x28 tile once, then draws the preview once at its new position.
- Cell interiors use fixed auxiliary/main byte masks derived from their exact DHGR positions. The edge masks preserve adjacent grid pixels while an opaque sprite write gives every interior byte a consistent phase; avoiding a general clipped-rectangle routine also keeps cc65 stack/arithmetic overhead out of the input path.
- Partial edge bytes are restored from generated per-cell scanline chunks copied from the original A2FM grid. Identical 24-row chunks are deduplicated into a compact pool; auxiliary writes never read the corresponding main-bank byte, preventing bank-crossing vertical trails in the center column.
- Generated low/high scanline tables feed 6502 assembly clear and opaque replacement loops. Movement performs only one masked 3-4 byte pass across 24 rows in each bank; all mask scanning, phase alignment, division, and modulo work happens during the host build.
- Horizontal lines set whole seven-pixel HGR bytes between masked edge bytes, vertical lines calculate `x / 7` once, and filled rectangles reuse the byte-oriented horizontal routine. Avoiding per-pixel 16-bit divide/modulo makes the initial grid appear substantially faster.
- A new current piece is generated after every valid placement and completed merge sequence. The hidden look-ahead queue and its three persistent bytes are removed; generation observes single-die mode directly.
- Sidebar slots are opaque fixed-position assembly blits. Missing second dice are replaced with black sprite planes, so pair-to-single transitions cannot leave stale pips or outlines.
- Placement snapshots all 25 logical cells and redraws the committed dice first. Merge resolution then snapshots and redraws only the cells changed by one connected group at a time; the bitmap grid is never cleared during normal play.
- An off-board second die is represented with an explicit sentinel. It must not inherit zero-initialized coordinates and mark board cell `(0,0)` as invalid.
- New-game rendering drains any pending keyboard latch before entering the game loop, preventing the title's start key from immediately placing a piece or starting another redraw.
- A later pass can unroll the four- and five-byte assembly loops if cycle measurements show a remaining input-path bottleneck.
- Page flipping is unavailable until the executable is moved out of HGR Page 2 at `$4000-$5FFF`.
- The linker reserves a `$0300`-byte cc65 software stack. Large game arrays and transfer buffers are static, and the smaller stack preserves enough heap for ProDOS asset opens below `$BF00`.

## Merge Callouts

- A merge awards the face value times the number of consumed dice. Removing sixes also awards a 50-point bonus, making a three-six merge worth 68 points. Every chain-reaction step updates the score and completes its own presentation before the next group is evaluated.
- The total uses a compact doubled 3x5 font. `generate_score_digits.py` emits position-specific auxiliary/main masks for its five fixed digit cells, and a language-card assembly blitter updates only digits that changed. Runtime score updates require no sprite construction, phase generation, division, or modulo operations; score travel animation is intentionally omitted to keep merges responsive.

## High Scores

- `HISCORE` is a 56-byte ProDOS file: `SIXH`, format version 1, an eight-bit checksum, and ten five-byte entries. Each entry stores three uppercase initials and a little-endian 16-bit score.
- New tables seed `DOM 1349`, `PRI 1020`, `TWD 893`, `TAN 802`, `TB 755`, `ACE 650`, `MAX 540`, `ZED 430`, `BOT 320`, and `CPU 210` in descending order; a trailing space pads `TB`.
- Game over loads and validates the table after the DHGR end screen has finished using the transfer buffer. Missing or damaged data becomes ten `--- 0` entries in RAM; a qualifying score shifts lower records, captures exactly three letters, recalculates the checksum, and truncates the existing file to the fixed format.
- The table reuses the 1 KB DHGR transfer buffer, adding no dedicated high-score array to BSS. The emulator launcher preserves the writable `HISCORE` file while replacing the rest of its working disk with the latest release build.

- Ten supplied comic callouts are preserved as source masters under `assets/merge_*_master.png`. `scripts/generate_merge_effects.py` corrects for DHGR pixel aspect ratio, reduces them to one-bit art, and emits deterministic previews.
- Each effect is restored to its original 280-signal by 48-scanline size. Its aligned auxiliary and main planes are 960 bytes each, so one plane fits the existing 1 KB transfer buffer and all ten effects consume 19.2 KB on disk.
- A successful merge chooses one callout and places its opaque rectangle in the screen quadrant opposite the merged cell. Horizontal and vertical sides are both inverted, guaranteeing that even a center-column merge is never covered. Before drawing it, a language-card routine saves the 1,920-byte background rectangle in unused auxiliary HGR Page 2. After 24 vertical blanks, a direct assembly copy restores both planes; no grid file reads or C-level die redraws occur while the display is live.
- `FIVES` is reserved for merges that consume face value 4 and create a five; `SIXIES` is reserved for merges that consume face value 5 and create a six. `AWESOME` is excluded from the first-merge random pool and identifies second-and-later generic merges within the same placement turn. Named five/six creation takes priority over `AWESOME` during a chain.
- Before the callout, the Apple II reproduces the C64 merge cross: four inverted 24x24 cell interiors travel along the destination row and column from the grid edges, clamp at the merged cell over five steps, and hold for two VBL frames per step. Duplicate cells at the destination are inverted only once, and a second XOR pass restores every underlying die and grid pixel exactly.
- Merges containing exactly three fives or exactly three sixes shake without Page 2 buffering. Compact language-card assembly circularly rotates the grid's 22-byte horizontal window across the 120 generated board-interior scanlines; the sequence moves right, crosses to left, and returns to center twice. Opposite rotations restore every byte exactly, while horizontal separators, score, mascot, and current/next side panels remain fixed.
- When the cross reaches its destination, a DHGR conversion of the C64 four-point firework sprite ignites over the resolved die. Three particles follow the original nine-frame side and center trajectories: they rise, spread 16 pixels to each side, reverse, and finish 32 scanlines below the merge before the callout appears.
- `MERGESTAR` stores seven signal-aligned phases of the sprite's 11 active rows in 616 bytes. A language-card XOR blitter at `$D400` draws and erases the particles at arbitrary DHGR coordinates, preserving every underlying die and grid signal without a save-under buffer.
- Merge effects are intentionally disk-backed rather than retained in BSS. The shared star and ten callouts preserve the precomputed dice blits and leave runtime memory below the `$BF00` high-memory limit.
- The linker reserves a `$0300`-byte C stack. This leaves enough heap above BSS for cc65's 1 KB ProDOS file buffer; a `$0400` stack causes asset opens to fail before reaching MLI.

GraphicsScientist confirms the build-time pre-shifting strategy used by the dice renderer. Its generator emits seven HGR pixel phases plus division/modulo lookup tables, while its sample blitter patches the destination store address once per scanline and then performs direct byte copies. SIXIES keeps its smaller five-phase set because dice only occupy the five fixed board-column alignments, and emits paired bank planes because DHGR interleaves auxiliary and main bytes. GraphicsScientist targets single-bank HGR rather than DHGR and has no explicit license file, so it is used as a design reference rather than copied into the build.

HiSprite takes precomputation further by compiling every horizontal shift into specialized 6502/65C02 instructions. It skips stores for fully empty bytes, emits cycle counts, and supports direct, XOR, or black-rectangle drawing; its demo erases old sprite rectangles before movement and redraw. That speed-for-code-size tradeoff is useful for arbitrary moving HGR sprites, but each SIXIES dice plane touches only three or four bytes on each of 24 rows at five fixed alignments. The existing compact data blitter therefore remains preferable to seven large generated routines per face. HiSprite is also single-bank HGR, does not provide DHGR bank management or pixel-level masked transparency, and has no explicit license file, so its source remains reference material only.

The Game Boy Tetris source demonstrates tentative state changes, collision rollback, a `needsRedraw` flag, background restoration, and page flipping. SIXIES adopts the state/redraw separation and background restoration, but not its Page 2 renderer: the current SIXIES executable occupies `$4000-$5FFF`. HiSprite, fdraw, and a2render are useful candidates for a later assembly blitter pass; no third-party rendering source is copied into this implementation.

The original Prince of Persia source is the strongest reference for a larger renderer: `LAYERSAVE` preserves the pixels beneath characters, `PEEL` restores them in reverse order, redraw buffers select changed blocks, and the frame is rebuilt in background/middle/foreground order. SIXIES uses the same principles at grid-cell granularity without copying its source. The repository's notice permits study but does not grant general franchise rights, so it remains a reference only.

## Sound

- The built-in speaker toggles whenever `$C030` is accessed.
- Pitch requires cycle-counted half-period loops; note duration requires an outer loop or equivalent sequencing.
- A blocking beeper tune consumes effectively all CPU time. It is suitable for a static title screen but not concurrent gameplay.
- Sound timing belongs in assembly. Game sound effects can use shorter, less pitch-critical loops.

## References

- [Double High Resolution Graphics - Pushing Limits](https://lukazi.blogspot.com/2017/03/double-high-resolution-graphics-dhgr.html)
- [Apple Extended 80-Column/AppleColor Card Manual](https://mirrors.apple2.org.za/Apple%20II%20Documentation%20Project/Interface%20Cards/Apple%20IIe/Apple%20IIe%20Extended%2080%20Column%20RGB%20Card/Manuals/Apple%20Ext80ColumnAppleColorCardHR%20Manual.pdf)
- [Apple II graphics: More than you wanted to know](https://nicole.express/2024/phasing-in-and-out-of-existence.html)
- [HIRES Graphics on Apple II](https://www.xtof.info/hires-graphics-apple-ii.html)
- [Apple II double buffering and double high resolution](https://retrocomputing.stackexchange.com/questions/19509/apple-ii-double-buffering-and-double-high-resolution)
- [Writing an Apple 2 game in 2021, Part 5](https://nick.zoic.org/art/writing-an-apple-2-game-in-2021-5/)
- [Making the Apple II sing](https://www.xtof.info/making-apple-ii-sing.html)
- [Best practices for animating Apple II HGR sprites](https://groups.google.com/g/comp.sys.apple2.programmer/c/T5wmM0jNWOY)
- [GraphicsScientist HGR sprite and image generator](https://github.com/blondie7575/GraphicsScientist)
- [Apple II Resources index](https://github.com/cbmeeks/Apple-II-Resources)
- [Game Boy Tetris for Apple II source](https://github.com/thelbane/Apple-II-Programs)
- [HiSprite HGR sprite compiler](https://github.com/blondie7575/HiSprite)
- [fdraw fast HGR graphics](https://github.com/fadden/fdraw)
- [a2render game rendering engine](https://github.com/martinhaye/a2render)
- [Original Prince of Persia Apple II source](https://github.com/jmechner/Prince-of-Persia-Apple-II)
