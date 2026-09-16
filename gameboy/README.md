# Sixies for Game Boy

Native Sixies for original Game Boy and Game Boy Color: Atari 800XL gameplay
and presentation, converted Sixies master artwork, and a user-provided Game Boy
title track. The cartridge is 128 KiB, MBC5 with 8 KiB
battery-backed SRAM. No Nintendo SDK or commercial boot ROM is required.

See [PORT_REVIEW.md](PORT_REVIEW.md) for the code comparison, asset provenance,
tests, and intentional differences from the computer versions.

## Cardinal rule: playing-area size

A one-pixel contrasting boundary marks the exact 160x144 display edges on gameplay,
title, intro, and game-over screens for layout inspection. The score sits one
tile farther left to stay clear of the right boundary. Source artwork is unchanged.
On the main grid page the boundary is pure black, with a dedicated Game Boy
Color palette so the green board and dice artwork keep their existing colors.

The approved playing area is locked: **5x5 cells, 20x20 pixels per cell,
100x100 pixels overall, with 18x18 dice canvases** and a one-pixel inset around
each canvas. Source art is never stretched. Moving the grid or preview must never resize them. Only an
explicit user request to change these dimensions overrides this rule.
See [AGENTS.md](AGENTS.md) for the persistent development constraint.

## Build and play

From the repository root:

```sh
make -C gameboy setup
make -C gameboy test
make -C gameboy test-emulator
make -C gameboy run
```

The ROM is `gameboy/build/sixies.gb`. `make -C gameboy run-mgba` opens mGBA
instead of SameBoy. Normal ROM builds use committed generated C assets; only
regeneration and emulator automation need the local Python environment.

## Controls

| Control | Gameplay action |
| --- | --- |
| D-pad | Move the placement cursor |
| A | Place the single die or ordered pair |
| B | Rotate a pair clockwise through four orientations |
| Start | Pause: resume, instructions, sound, flash setting, new game |

Development cheat: during gameplay enter Up, Up, Down, Down, Left, Right,
Left, Right, B, A to jump directly to Game Over. It is compiled only by
`make run`, `make run-mgba`, or `make DEBUG_CHEATS=1`; release builds exclude it.

During the opening spiral and blocking merge effects, the latest D-pad move or
B rotation is buffered and applied when play resumes. Placement is never buffered:
press A again after the effect to place the next piece. Occupied preview targets
show a steady diagonal hatch; an empty partner keeps blinking. Pairs extending
off the board show the same hatch at their visible origin. The sound-linked invalid-placement
mascot in the Next window still requires a rejected A press and lasts 19 VBlanks.

Merge ripples converge from the board edges in five steps, adding diagonal arms
for fives and sixes. Three stars rise and fall through nine two-frame steps;
six-clears flash for five frames. Merging fives or sixes also shakes only the
grid two pixels right and back, twice, without moving the Next window, score,
or screen border. Fours do not shake. Reduced flashing suppresses the opening spiral,
grid shake, palette flash, ripple, and stars without removing score feedback.
The one-second chain-reaction badge remains nonblocking.

The native Studio313 intro appears for four seconds at startup and can be
skipped with A/Start. On the title, A/Start opens the start menu; B opens credits. `Press Start`
uses Roberto Mocci's Morbidosa bitmap font, centered below the logo at y=116.
The original font files and SIL Open Font License are in `assets/fonts/morbidosa/`.
The prompt
appears immediately whenever the title opens, then alternates 0.5 seconds visible
and 0.5 seconds hidden (30 frames per phase). The attract sequence cycles
title (11 seconds), top ten (5 seconds), and credits (11 seconds). Credits use
the supplied full-screen card as a fixed illustrated dice frame; native
Morbidosa text fades in, holds, and fades out across the plain panel.
How to Play uses the supplied `instructions_sixies160x144.png`, stored as
`assets/instructions_master.png`, in place of the six legacy diagram pages.
The single full-screen bitmap retains its native 160x144 layout, decorative
heading, mascot, frame, and dice diagram. The footer caption and its separators
are removed, leaving a clean background between the corner decorations. The five rules use
the native Itty Bitty font from `assets/font_itty_bitty_master.png`, with solid
dark lettering on a clean light background; the source PNG stays unchanged.
Conversion uses four nearest-color, undithered shades and exact tile deduplication,
with source-derived greens on CGB and grayscale on DMG; no resizing or tile
approximation is applied. A, B, or Start returns to the start menu or pause menu.
Left/Right stays on the same screen. `make assets` regenerates
`build/previews/instructions-1.png` and `instructions-sheet.png`.
New game from the pause menu requires confirmation.
High scores use three initials: Up/Down changes a letter, Left/Right selects,
A advances/confirms, and Start saves immediately.
The supplied `highscore160x144.png` template is stored as `assets/highscore_master.png`.
Its header, mascot, and score-panel layout frame five live entries at a time;
Left/Right switches between ranks 1–5 and 6–10. Scores retain all five digits,
and the browsing footer is blank. On page one, only the highest-scoring row's
rank, initials, and score sway three pixels left/right after a one-second
pause. The panel, other rows, and artwork stay fixed. Returning to page one
restarts the pause; initials entry remains stationary with its control hints.
Values up to 65535 display in full. A qualifying game opens the appropriate page with the player's
row highlighted and the active initial inverted. Up/Down wraps A–Z, B moves
back a letter, and A on the third initial or Start saves to battery memory.
The existing ten-entry save format and previously saved scores are preserved.

Game Over stays visible for 1.5 seconds (90 frames), or until a fresh A/B press.
The supplied `Game_Over_New_moddified_160x144_New.png` results artwork then shows
the final score and best score, using a dedicated four-color muted-green palette.
Use Up/Down to choose **Try Again** or **Main Menu**, then A/Start to confirm;
B is a shortcut to Main Menu. A held splash-skip button cannot also choose a
menu option. Qualifying scores still receive initials entry before the selected
action runs. Try Again starts a fresh game; Main Menu returns to the start menu.

The start menu uses the supplied `Sixies_Menu_New160x144.png` artwork, stored as
`assets/start_menu_master.png`. Up/Down moves the arrow and highlight; A/Start
confirms **Play**, **Settings**, **How to Play**, or **High Scores**. Play starts
the game directly. Settings saves sound and reduced-flashing preferences;
instructions and high scores return to the same menu selection. B returns to
the title. Holding Start on the title cannot accidentally activate Play.
Menu labels and the bottom tagline are protected from lossy tile reduction.

Settings uses the supplied `settings_rebuit.png` template, retained as
`assets/settings_master.png` and converted to 160x144 with four undithered shades.
Its decorative heading, mascot and frame remain; the bottom caption and separators
are removed. Sound/Flash labels and live ON/OFF values use native Itty Bitty text.
Up/Down selects a row, Left sets it OFF, and Right sets it ON. A does not toggle;
B or Start returns to the start menu. FLASH OFF enables the existing reduced-flashing
mode; FLASH ON restores full effects. Both preferences persist to battery memory,
with no extra save when a control is already at the requested value.
The screen's 224 tiles load once; input updates only the 8x4-tile options area,
so the artwork stays fixed and font tiles are not reloaded during navigation.
`make assets` produces `build/previews/settings-0.png` through `settings-7.png`.

The pause screen uses the supplied artwork in `assets/pause_master.png`, scaled
to 160x144. Its frame, headings, pause bubble and mascot remain; live menu labels,
the selection marker and footer use native Itty Bitty lettering. Up/Down selects
Resume, Instructions, Sound, Flash or New Game. A chooses/toggles the selected
option, while B or Start resumes play. Sound ON/OFF and Flash FULL/REDUCED reflect
the saved preferences; New Game still requires confirmation. The tile atlas loads
once, and navigation updates only the cursor and setting-value tilemaps, avoiding
font reloads or changes to the surrounding artwork. The twenty selection/settings
combinations are generated as `build/previews/pause-0.png` through `pause-19.png`.

The start menu, confirmation screen and game-over results/options use the supplied
Lanky Git Variable L font (`assets/font_lanky_master.png`). Black/dark glyph
pixels are extracted at their native eight-pixel height; magenta width guides
and the pale atlas background never enter the font. Proportional menu labels
and wider score fields retain the full glyphs, including wide initials and
five-digit scores. Editing initials uses a small sprite overlay for responsive
input; saved initials and scores keep their existing format. High-score ranks,
initials, scores, and entry hints use the earlier compact five-pixel-tall font
from `assets/font_itty_bitty_master.png`, rather than the taller Lanky font.
The highest-score row still sways after one second, and its logo is unchanged.
The illustrated game-over splash and decorative Sixies/high-score logos are
unchanged, as is the gameplay font. How to Play uses Itty Bitty for its small text.
Selected and unselected menu text retain identical lettering; only the
highlight changes. Emulator tests compare these pixels with the source artwork
after navigation and returning from submenus.

## Rules and probability table

- The board is 5x5. Place only into empty cells; diagonal neighbors do not match.
- Three or more equal connected dice merge at the placed origin. Faces 1-5
  advance by one; sixes disappear. The entire connected group participates.
- A pair resolves its first die, including chains, before its second die if
  that cell survived. Chain depth continues across both dice.
- Award `(face × connected count + bonus) × chain depth`, beginning at depth 1.
  Making five adds 25, making six adds 50, and clearing sixes adds 100.
  Scores retain the original unsigned 16-bit wraparound behavior.
- Merge at least four fours in one group to unlock single 4 and pair 3+4.
  Clear at least four sixes in one group to unlock single 5 and pair 4+5.
  These independent milestones last until the next game.
- If no adjacent empty pair fits, deal a matching single. Game over means the
  generated piece has no valid placement, not merely that a pair cannot fit.

### Probability Table 1: pre-four deals

Before the four milestone, and outside temporary four-pressure or
crowded-board rescue, normal deals use the supplied 39-appearance table below.
Pair order is meaningful: `2+1` is a different deal from `1+2`. A blank four
is an explicit zero-weight row.

| Deal | Appearances | Overall chance |
| --- | ---: | ---: |
| 1 | 5 | 5/39 (12.8%) |
| 2 | 3 | 3/39 (7.7%) |
| 3 | 1 | 1/39 (2.6%) |
| 4 | 0 | 0% |
| 1+1 | 0 | 0% |
| 1+2 | 5 | 5/39 (12.8%) |
| 1+3 | 8 | 8/39 (20.5%) |
| 2+1 | 10 | 10/39 (25.6%) |
| 2+2 | 0 | 0% |
| 2+3 | 1 | 1/39 (2.6%) |
| 3+1 | 4 | 4/39 (10.3%) |
| 3+2 | 2 | 2/39 (5.1%) |
| 3+3 | 0 | 0% |
| **Total** | **39** | **100%** |

Singles total 9/39 (23.1%) and ordered pairs total 30/39 (76.9%). All omitted
pre-four single/pair rows are zero-weight. The later milestone, pressure, and
crowded-board rules below use their own deal pools.

Permanent unlocks add their pair to the non-3+3 pool, which shares 70% of normal
deals; 3+3 keeps 5%. Available singles share the 25% single pool equally.

Four or more visible fours activate temporary four-pressure, regardless of the
permanent four milestone: 3+4 gets 35%, 3+3 gets 5%, and other eligible pairs
share 35%. Single weights are `1,2,3,3,4,4,4,4,4,4`, changing the final 4 to 5
when fives are unlocked. Pressure ends when fewer than four fours remain.

At 18-21 occupied cells, 50% of deals first attempt a matching single; at
22-24 cells, 75% do. Without adjacent empties the attempt is mandatory. Match
weights count each empty orthogonal neighbor of every eligible die. Faces 1-3
are always eligible, 4 needs its unlock or pressure, and 5 needs its unlock.
If there is no eligible neighbor, use the current single pool. Sixes are never
dealt. The generator follows the Atari/Apple II four-byte RNG and roll order.

## Presentation and persistence

The port includes the supplied native 160x144 `title_screen-Main.png` title screen
(stored as `assets/title_master.png`, using its four main colors) and
the supplied Ittiest Bittiest Clean Variable D native 8x8 font, plus the
transparent green pixel-art credits logo, top-ten mascot, dice, grid rails,
game-over art, ten supplied 64x32 comic
callouts, chain-reaction sprite, and star artwork. DMG uses four shades; GBC title,
intro, and game-over screens preserve their native four-color palettes. Menus use a light
background with dark text. Gameplay uses a light-green background
across the full screen. The supplied grid style becomes a 100x100 board inset
exactly 22 pixels from the top and five from the left, with five connected 20x20
cells per side. Board and preview dice use 18x18 canvases,
with a one-pixel inset on each side of a board canvas. Pixel scrolling
preserves the full board size; sprite effects use the same inset. The preview
frame is 48x48 pixels at x=109, y=78, close to the board's lower-right corner.
Its 36x36 interior shows pairs in the same orientation and face order as the
hovering dice through all four rotations; single canvases are centered at (124, 93).
The old connector tab and bridge are removed, leaving a clean frame and light
background between the board and preview. Gameplay font ink
shifts one pixel within its tiles so the last
score digit remains visible. Other screens reset the scroll position.
Faces 3, 4 and 6 use `assets/dice/three_18x18.png`, `assets/dice/four_18x18.png` and
`assets/dice/six_18x18.png`, the supplied native 18x18 sources, without cropping
or resampling. Their hover variants reverse the opaque shades; off-grid previews
use the shared invalid hatch instead of the legacy X variants. Transparency maps to the light board background.
The four-face source's dark top and bottom outlines have alpha values below the usual
128 cutoff. The shared frame converter makes only their nontransparent pixels opaque
before generating normal, hover and invalid tiles, preserving the missing edge
without changing the source PNG or interior rows. The two- and five-face rebuilds
inherit the same correction. Both edges match the three-face reference in
normal, hover and invalid states.
Face 1 uses `assets/dice/one_18x18.png`, rebuilt with the three-face die's exact
18x18 silhouette, outline and bevel, replacing only the center with one solid
3x3 pip. Recreate it with
`.tools/gameboy/venv/bin/python gameboy/scripts/rebuild-one-die.py` from the
repository root. This replaces the smaller body inside the old 18x18 canvas;
no scaling or extra padding is applied. The earlier source is retained as
`assets/dice/one_18x18_original.png`.
Face 2 uses a matching rebuild in `assets/dice/two_18x18.png` with two solid
3x3 diagonal pips. Recreate it with
`.tools/gameboy/venv/bin/python gameboy/scripts/rebuild-two-die.py` from the
repository root. The earlier source is retained as `assets/dice/two_18x18_original.png`.
Both the two- and five-face rebuilds share `scripts/dice_frame.py`, preserving
the exact four-face outline, bevel and restored top/bottom edges with no extra padding.
Face 5 uses `assets/dice/five_18x18.png`, a readability-focused redraw with
five separated, solid 3x3 dark pips on a light olive face. Its transparent
18x18 final asset is sampled without resizing in gameplay, Next and effects.
Recreate it with `.tools/gameboy/venv/bin/python gameboy/scripts/rebuild-five-die.py`
from the repository root. The rebuild copies the approved four-face outline,
bevel, transparency and restored top/bottom edges at their native coordinates, replacing
only the central face with five high-contrast pips. No resizing or additional
padding is used, so its border matches the other dice rather than leaving a
light ring around a smaller body. The earlier AI master and prompt are retained
as historical references, but are no longer used by the rebuild.
It uses the same hover inversion and off-grid hatch as the other native faces.
All six final assets use the existing four-green gameplay palette; the old
16x16 sheet and earlier individual masters are retained but inactive.
The converter now gives each face a consistent, distinct shading using
`scripts/dice_shading.py`: light with dark pips for 1/2/5, dark with light pips
for 3/4/6. The original 18x18 PNGs, silhouettes and pip positions are unchanged;
only opaque shade indices are remapped. Board and Next share these styles, and
hover inversion is applied afterward. No dithering is needed for these six
high-contrast selections. This is per-face styling, not random per-piece colors.
`make assets` also creates `build/previews/dice-24-shadings.png`, showing all
24 permutations of the four shades on all six faces, and
`build/previews/dice-selected-shadings.png`, showing the six active choices.
The comparison includes low-contrast permutations for reference; only the
selected six are baked into the ROM, with no extra runtime tiles or palette changes.
Off-grid pairs use the shared invalid hatch. A rejected A-button placement briefly
replaces the Next dice with the supplied falling mascot
(`assets/invalid_placement_master.png`), fitted over the unchanged 48x48 frame.
The overlay runs only alongside the invalid-move sound for 19 VBlanks (about
0.32 seconds), then restores the dice even if the cursor remains invalid.
Hovering, rotation, and muted attempts do not trigger it. Invalid A presses
do not change the board or score. The overlay temporarily reuses only the 32-tile
background preview pool (15-46), independently of chain sprites and callout tiles.
Next composites its frame and dice using pre-shifted native pixel rows in bank 7,
uses precomputed tile maps for all 150 single/pair orientations to avoid runtime
tile comparisons, and caches the most recent normal preview for prompt
restoration when the invalid sound ends. Asset generation checks every pair and
rotation against the pool limit; the outer 48x48 frame stays at (109, 78).
Green rail profiles and the rounded double frame are sampled from the mock-up;
the four outer board corners are rounded separately so internal rails stay
connected. The light background matches the supplied artwork. The preview
label remains removed.
The gameplay logo, brick floor, and animated mascot are omitted from the main
grid screen to reserve the surrounding area for the expanded board.

Gameplay uses a 104x104 tile canvas for the 100x100 board. The renderer combines
20-pixel cell rows in a 2,704-byte buffer, preserving neighboring pixels where
cells share hardware tiles. Pre-shifted cell rows live in ROM bank 7; only
the nine tiles touched by an updated cell are uploaded. Signed background
tiles 55-223 hold the canvas and 224-247 hold the framed score panel. A compact gameplay-only HUD atlas keeps the score readable while freeing space
for the larger canvas; menus and sprite effects retain their full font atlases. Chain sprites use the separate sprite-only tiles 40-74,
so displaying a chain cannot overwrite the board or preview artwork.

The main playing screen has a subtle light-dot background outside the board,
Next window and score panel. Its dedicated tile 255 and CGB palette 3 keep it
separate from dice, grid flashing and callout effects.
The score is enclosed in a 48x32 panel at (109,14), eight pixels above the grid,
using the same beveled
border artwork as Next. The Itty Bitty SCORE label and five digits are centered
inside. Score tile
uploads are cached until the value changes or gameplay is entered again.
Exclamation words are fitted from their original artwork into the 48x24 sidebar
gap at (109,46), between Score and Next, after the flying points award clears. They no
longer cover the grid. They temporarily use HUD tiles 1-14 and spare tiles 248-251;
the HUD font, background and palettes are restored afterward. Their half-second
display time and suppression during chain reactions are unchanged. The 100x100
board and 48x48 Next window remain unchanged.

Free in-bounds hovering dice use a nonblocking normal/inverted cycle. The C64's
`src/grid_base.asm` updates a four-phase marching border every four frames;
Game Boy adapts that 16-frame cycle to eight VBlanks inverted, eight normal.
Both hovering dice share a phase; settled dice and Next remain unchanged.
An empty partner keeps blinking even when the other target is occupied.
Invalid hatching feedback stays steady for occupied cells and off-grid pairs. Reduced flashing keeps a static
inverted hover. The cycle begins after the opening spiral and stops during
merge effects and on other screens.
Effects include the opening spiral, inward row/column ripple, diagonal arms
for face-5/6 merges, grid-only shake, six-clear inversion, three-star particles,
multiplied awards, moving chain badges, and a nonblocking chain-reaction sprite held for one second
with a solid oval and transparent exterior, positioned in the grid quadrant
opposite the merged die. Comic exclamation callouts appear for normal merges
but are suppressed when the chain-reaction sprite is active. Native
audio cues cover movement, rotation, placement, invalid moves, and merges.
Reduced flashing omits the spiral, ripple, stars, and six-clear inversion;
score and chain feedback remain. Sound and reduced-flash settings are saved.

Chain reactions also launch three short firecracker bursts from the merged die
over 60 VBlanks (about one second), using the supplied yellow and green star
designs with transparent backgrounds. Three 8x8 particles spread and fall while
play continues behind the badge. OBJ tiles 78-79 and sprites 0-2 are reserved
for this effect; together with the badge this stays within the ten-sprites-per-line
limit. Bursts stop on screen changes or a new merge, and are omitted with reduced
flashing. The converted art preview is `build/previews/chain-stars.png`.

The opening grid pulse matches the Atari 800XL sequence: it starts at the
bottom-left, travels clockwise in an inward spiral, and restores the center
last. Each cell now holds for one VBlank instead of two, shortening the opening
without changing the path. The hovering board dice appear only after that final center pulse, while
the independent next-piece display remains visible throughout.

Merge points follow the C64's `AddAnimatedGroupScore` / `AnimateMergeScoreSprite`
in `src/assets/merge_chain_sounds.asm`: hold above the merged die for three
frames, travel diagonally to the scoreboard, update the displayed total on
arrival, then hold two frames before hiding. Game Boy uses four-pixel horizontal
and upward steps (two pixels downward when starting above the destination),
scaled from the C64's eight/eight/four-pixel movement. The actual awarded value,
including bonuses and chain multipliers, appears without leading zeroes, with
a light outline for contrast. It uses OBJ tiles 75-77 and up to three sprites,
separate from chain-badge artwork. Reduced flashing shows a stationary award
instead. Score arithmetic, saving and buffered controls are unchanged.

The title/attract sequence loops a compact hUGETracker conversion of the
user-provided `We are the Reason` MIDI. The source file does not identify a
rights holder, so use it only where the appropriate music rights have been
cleared. The native public-domain hUGEDriver plays it during attract mode and
releases the audio channels before menus and gameplay. The Sound setting disables
both this track and the native UI/gameplay effects. The original design/code/art
credit remains **DSKILTON, Studio313 Games, 2026**.

The top ten starts with the Atari entries and accepts three-letter initials.
Two checksummed SRAM records alternate writes, with a final commit byte, so
an interrupted update can fall back to the prior record. Old Game Boy
strawman best-score saves migrate as `OLD` when they qualify. Emulator battery
files sit alongside the ROM; `make clean` deliberately preserves them.

## Tools and asset workflow

| Tool | Purpose |
| --- | --- |
| GBDK-2020 4.5.0 | Pinned compiler, linker, png2asset, romusage |
| RGBDS 0.6.1 | Pinned hUGEDriver-to-SDCC conversion; desktop RGBDS also provides general SM83 utilities |
| SameBoy / mGBA | Interactive emulation and debugger cross-checking |
| Tiled | Tilemap authoring |
| hUGETracker 1.0.11 | Edit and export the title track |
| GB Studio 4.3.2 | Optional visual scene, sprite, and interaction prototyping |
| Piskel Web | Optional animated sprite and pixel-art authoring |
| GIMP | Optional raster editing, cleanup, and sprite preparation |
| [Retro Palette Studio 3.6](https://nowintime.itch.io/retro-palette-studio) | Optional Game Boy palette design and export |
| Pillow 11.3.0 | Deterministic art conversion |
| PyBoy 2.7.0 | Headless DMG/CGB gameplay, audio, and save regression tests |

`setup` installs the checksum-pinned compiler and tracker under
`.tools/gameboy`, macOS desktop tools through Homebrew, and a local Python venv.
Desktop applications are skipped on Linux. Existing desktop installations are
retained. The unsigned upstream macOS hUGETracker may need Control-click/Open;
its Intel build uses Rosetta on Apple Silicon.

GB Studio is an optional companion editor, not part of the reproducible ROM
build. Sixies is a native GBDK C project rather than a `.gbsproj`, so GB Studio
cannot open it directly; use GB Studio for visual prototyping and transfer
approved assets or behavior into the native source and conversion pipeline.
Piskel is installed as a dedicated Chrome web-app launcher because upstream
recommends the current browser editor over its outdated, limited-QA desktop
build. Export lossless PNG spritesheets and pass them through the existing
asset conversion pipeline; Piskel output is not linked directly into the ROM.
GIMP is an optional raster editor for preparing source artwork; retain native
pixel dimensions and export lossless PNGs for the conversion pipeline.
[Retro Palette Studio 3.6](https://nowintime.itch.io/retro-palette-studio) is
an optional external palette-authoring companion; review and convert exported
colors through the existing deterministic asset pipeline before adding them to
the ROM.

```sh
make -C gameboy setup-assets    # Python converters and emulator only
make -C gameboy assets          # Shared PNG/assembly art -> native 2bpp C tiles
make -C gameboy doctor-desktop  # Check installed tools
make -C gameboy music           # Open hUGETracker
make -C gameboy clean           # Remove binaries/symbols, preserve saves
```

`assets/title_music.uge` is an unverified user-provided MIDI conversion and
`src/generated_title_music.c` is its bank-3 export. Release builds exclude both
from the ROM until a licensed replacement is approved. Developer runs and emulator
tests include it with `TITLE_MUSIC=1`. hUGEDriver is vendored in
`vendor/hUGEDriver/` under its public-domain dedication. The build
installs its own pinned RGBDS 0.6.1 converter because hUGEDriver's SDCC bridge
uses that object format; desktop RGBDS remains available separately for general
assembly work.

Edit the shared masters listed in the port review, then regenerate and commit
the generated C/header files. Artwork previews go to `build/previews/` and
emulator tests write actual 160x144 screens to `build/screenshots/`.

## Verification and GitHub

`make test` runs host rules and save-format tests, validates the exact 128 KiB
cartridge/header size code and checksums, and reports ROM/RAM bank use.
`make test-emulator` exercises both DMG
and CGB through attract screens, instructions, gameplay, chain reactions,
six-clear, pause/settings, initials, persistence, and damaged-save recovery.

`.github/workflows/gameboy.yml` regenerates and checks every generated C asset
and the generated header, runs the host and emulator tests, and uploads the ROM,
`.map`, `.noi`, `.sym`, and screenshots. Shared art changes also trigger the
workflow.

Local emulator checks pass; physical DMG/GBC and flash-cartridge validation
remain a release gate. Use SameBoy Developer Mode with `build/sixies.sym`, and
cross-check in mGBA before hardware testing.
