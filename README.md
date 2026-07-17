![StarwarsScrollerDemo running in VICE](docs/StarwarsScrollerDemo.png)

# StarwarsScrollerDemo

Standalone C64 Starwars Demo scroller intro inspired by Raistlin's write-up and
the Nobounds / Genesis Project Starwars part.

Current highlights:

- Full native ACME Star Wars-style perspective bitmap scroller.
- Vector title opening with rotating Imperial emblem highlight.
- Plasma/Vader intro with SID music, dissolving plasma text, and orbiting TIE sprites.
- Automatic handoff from `PARALAX` after a five-second hold, with Space as an early skip.
- Opposing TIE fighter and X-wing transition with Imperial/Rebel bitmap emblems.
- Death Star / RetroDNA banner cycle above the crawl.
- Two-font crawl text using build-time `[1]` and `[2]` markers.
- Exomizer-crunched single-file PRG plus D64 and Sparkle2 packaging paths.

Latest local crunched size after the Vader dithering pass:
`build/StarwarsScrollerDemo-sfx.prg` is 26,967 bytes.

The primary `build/StarwarsScrollerDemo.prg` target is a native ACME port of the
technique from the NoBounds Starwars part (`Starwars.cpp` in the public
release): a hires-bitmap crawl with real pixel-level perspective.
`scripts/generate_tables.py` builds a 16x16 font from a small set of unique
16px row segments, precomputes bit-picked FontData tables for every
(screen line, byte, source column) the perspective mapping needs, and emits a
fully unrolled plotter. At runtime the scrolltext streams through 16 cyclic
256-byte column buffers as font-row indices; the plotter samples them with
`ldy ScrollData+col,x / lda FontData_a,y / and FontData_b,y / sta bitmap`,
skipping more source rows per screen line near the horizon. Background is
1-bits and ink is 0-bits, so overlapping glyph halves combine with `AND`.
The vector and plasma opening plays "Gearshift" (see below) from a dedicated
50 Hz raster IRQ, independent of the visual renderer. After
the ship transition, the scroller plays "Galway Nights" from a raster interrupt
so the tune keeps 50 Hz timing while the plotter runs longer than a frame.
`scripts/generate_logo.py` converts `src/assets/deathstar_logo.png`
into hires bitmap data that is AND-merged over the starfield in the 80-pixel
banner area above the crawl, with per-cell C64 ink colours chosen from the
source image. The native PRG opens in true hires bitmap mode with the
supplied `STAR / RETRODNA / WARS` artwork traced into editable SVG paths by
`scripts/vectorize_star_retro_war.py`, then rasterized from that geometry into
a full-screen C64 hires image. A large light-blue/gray dithered rendering of
`imperial_emblem_vector.svg` sits behind the title, with the stepped animated
vector retained separately as `imperial_emblem_rotoscope.svg`. On the C64, an
eight-phase light-blue dither highlight rotates through emblem-only cells about
once every 1.1 seconds, creating motion without modifying foreground letters.
After the initial fade, `STAR / RETRODNA / WARS` and the rotating emblem hold
for five seconds. A short ordered fade replaces them with the cleaner outlined
`A / RETRODNA / PRODUCTION` contours extracted from
`a_retrodna_production_source.png`; this second card has a plain black
background and holds for three seconds. Its bitmap and compressed two-bit
color map fit in the remaining RAM beneath I/O. The replacement then fades out.
The initial compressed bitmap expands
in place at `$e000`; Color RAM preserves the target per-cell palette while the
original plasma screen is temporarily backed up at `$0400`.
The next scene opens in true hires bitmap mode with the
perspective-preserving `vader2` portrait over a full-screen field of solid
circular plasma pixels. The portrait is shifted left by eleven 8x8 cells so the
helmet meets the border, the pink cape edge is hidden, and the neck remains on
the bottom border. `scripts/generate_vader2.py` uses the Death Star converter's
4x4 Bayer threshold but restricts Vader to a monochrome C64 ramp: black, dark
gray, gray, and light gray. Pure white is deliberately excluded so helmet and
cape highlights are carried by dither density instead of hard 8x8 white color
cell corners. This removes the colored/right-angle artifacts that appeared when
individual cells selected purple, blue, or bright white inks. `scripts/generate_pilot_hires.py`
composites those cells over the staggered plasma and phase field. Color RAM,
which hires mode does not display, serves as a temporary packed-distance lookup
page. Separate Exomizer memory streams keep the 8 KB opening bitmap, 500-byte
visibility field, and later 3,840-byte title inside the existing temporary
workspaces; the official Exomizer 3 decruncher is vendored in
`src/third_party/exomizer` with its original license notice.
The two radial ripples retain additive interference but use separate color
sequences: the first moves through blue and cyan, while the second moves through
purple, red, light red, orange, and yellow according to the locally dominant
wave amplitude.
After five seconds of clear plasma, the red plasma titles `RETRODNA`, `AND`, and
`PARALAX` assemble dot by dot in a pseudo-random dissolve pattern. Each word
except the last holds for three seconds, disperses through the same pattern,
and leaves two seconds of clear plasma before the next title. `PARALAX` remains
intact for five seconds and then advances automatically to the ship transition;
Space remains an early skip. A temporary per-cell backup restores the
Vader bitmap, screen colors, and live ripple phase behind every removed dot.
Eight expanded 48x42 multicolor hardware sprites orbit over the plasma on a
64-position path. Each self-contained sprite combines an opaque dark-blue
circle with its light-gray TIE fighter, while four symmetric frames provide
rotation.
The TIE squadron orbits and rotates continuously throughout the plasma scene.
The sprites are evenly spaced in front of the plasma and fade through the C64
black, dark-gray, gray, and light-gray ramp. Vader changes their priority on
the left side and fully hides the deepest pass. At startup the compressed
intro-logo stream is shadowed at `$0400`, freeing `$c400-$c4ff` for the four
temporary sprite frames until Space begins the ship transition.
After the automatic hold or an early Space press, the opening cuts to
source-derived 48x42 TIE fighter and X-wing composites crossing in opposite
directions over transition-only Imperial and Rebel bitmap emblems. Each ship
uses four synchronized sprite bobs with layered hires detail and carved
negative space; a raster split reuses all eight sprites for the lower X-wing.
Both cross the same hires starfield used by the main part, with the upper star
pattern repeated behind the X-wing. The transition emblems are cleared before
the main Death Star setup resumes. After the flyby, the completed bitmap is
revealed from the centre out. During that reveal,
`scripts/generate_intro_logo.py` displays the
supplied `STAR WARS` artwork as a 320x96 hires image beneath the Death Star. It
remains fully visible for 150 PAL frames, fades through four cumulative Bayer
phases, and then releases its temporary `$7800-$86ff` storage to the cyclic
scroll buffers so the crawl can begin. The Death Star banner then fades through
four Bayer-dither phases and a textured RetroDNA logo drops into the same
320x80 area. Its letter faces
contain Death Star paneling and directional highlights preserved through the
same Bayer conversion, with blue and purple reserved for recessed shadows.
Each completed banner remains visible for ten seconds before the cycle repeats.
Integration details live in
[`docs/ship-transition.md`](docs/ship-transition.md).

"Gearshift" starts with the vector title and continues through the plasma
scene. Pressing Space starts the 90-frame ship flyby and fades its SID master
volume to silence over the first 45 transition frames. A 1,042-byte compressed
"Galway Nights" overlay is then restored from RAM beneath I/O to `$9000`, ready
for the main scroller's raster IRQ player.

`build/StarwarsScrollerDemo-loader.prg` is an
alternative path that loads the vendored, original Nobounds-generated part
from disk, phase-locks CIA2 Timer B for its stable raster code, and jumps
into the original Starwars entry point at `$9fcc`.

Build:

```bash
./scripts/build.sh
```

Toolchain:

- ACME assembler
- Python 3
- VICE `c1541`, optional for D64 packaging
- Exomizer 3.1.2, required for compressed intro assets and `build/StarwarsScrollerDemo-sfx.prg` (`/opt/homebrew/bin/exomizer` when installed through Homebrew)
- Mono or Wine, optional for running Sparkle2 locally

Build a Sparkle2 packaging script and, when Mono or Wine is available, a
Sparkle-linked D64:

```bash
make sparkle
```

Run in VICE, when installed:

```bash
./scripts/run.sh
```

The default run path injects and autostarts
`build/StarwarsScrollerDemo-sfx.prg`, the Exomizer-packed bitmap scroller.
Explicit VICE PRG inject mode prevents saved emulator preferences from mounting
the program as a temporary disk and leaving the demo at `SEARCHING/LOADING`.

An optional five-sprite `STARWARS` title is retained in the source but disabled
in the default presentation. It was rasterized from shadowyblade's logo-only
Star Wars font and can enter expanded at the wide bottom of the crawl before
contracting near the horizon. The active crawl alphabet comes from
`src/assets/scroller_charset.a`: the table generator maps
its A-Z, numeric, and punctuation glyphs from 8x8 charset cells into the
crawl's 16x16 source cells. Five horizontal samples keep the font compatible
with the unrolled plotter's compact FontData vocabulary. Scroller text can use
build-time `[1]` and `[2]` markers: `[1]` selects the project charset and `[2]`
selects the stock C64 character ROM from `chargen-901225-01.bin`. The markers
are stripped before `scroll_text` is emitted.
The logo title's original OTF is not vendored. Its embedded license is Creative
Commons BY-NC-ND 3.0;
source attribution: `https://fontstruct.com/fontstructions/show/470284/star_wars_27`.

To test the packaged D64 loader for the original Nobounds-generated part:

```bash
RUN_D64=1 ./scripts/run.sh
```

Output:

- `build/StarwarsScrollerDemo-sfx.prg` -- Exomizer-crunched single-file build, current local size 26,967 bytes
- `build/better-off-alone-markov.sid` -- continuously looping 137 BPM PAL PSID
- `build/galway-nights.sid` -- original Martin Galway style 107 BPM PAL PSID
- `build/galway-nights.prg` -- standalone runnable driver for the same tune
- `build/dark-armada.sid` -- slow-building original motif-Markov military PSID
- `build/dark-armada.prg` -- standalone runnable driver for the same tune
- `build/gearshift-markov.sid` -- punchy original 125 BPM motif-Markov PSID
- `build/gearshift-markov.prg` -- standalone runnable driver for the same tune
- `build/StarwarsScrollerDemo.prg` -- native bitmap perspective scroller
- `build/StarwarsScrollerDemo-sparkle-part.prg` -- Sparkle2 payload, assembled at `$080d`
- `build/StarwarsScrollerDemo-loader.prg` -- D64 loader for the original Nobounds part
- `build/StarwarsScrollerDemo-direct.prg` -- monitor-preload runner for the original part
- `build/StarwarsScrollerDemo.d64`
- `build/StarwarsScrollerDemo.sls` -- Sparkle2 loader script
- `build/StarwarsScrollerDemo-sparkle.d64` -- Sparkle2 disk, when Sparkle2 can run locally

The looping SID is built by `scripts/generate_midi_markov_sid.py` from the
supplied 20-second MP3 reference. The first stage detects 137 BPM, transcribes
quantised lead, bass, and drum events, and writes the real format-1 Standard
MIDI file `src/music/better_off_alone_source.mid`. The second stage parses that
MIDI, learns a deterministic second-order Markov chain with first-order
backoff, and writes `src/music/better_off_alone_markov.json`. The final stage
renders a closed 64-sixteenth-note Markov walk as a 350-frame (7.00-second)
three-voice SID phrase. The lead uses PWM, voice 2 supplies filtered chord
arpeggios, and voice 3 is time-shared between triangle bass, pitch-drop kick
accents, and pitched-noise snare. At frame 350 the player immediately returns
to frame zero, so SID playback continues without a silent tail. Its PSID
init/play addresses are `$1000` and `$1080`. Re-transcribing the MP3 requires
ffmpeg and NumPy; rebuilding from the saved MIDI requires only Python's
standard library.

"Galway Nights" is an original tune in the style of Martin Galway, built by
`scripts/generate_galway_sid.py` and `src/music/galway_nights.a`. It is a
16-bar, 35.84-second seamless loop at ~107 BPM loader pace: one syncopated
hook restated down an Andalusian Am-G-F-E descent. Voice 1 carries the hook on a pulse
lead with a swept width and Galway's signature delayed vibrato, which stays
flat for the first fifth of a second of each note and then blooms quickly
through three depth steps to a deep wobble. Voice 2 repeats the lead a dotted eighth
later at half sustain (the Ocean-loader echo). Voice 3 time-shares a bouncy
octave pulse bass with a pitch-drop triangle kick and noise snare: a straight
backbeat under the hook, a busier loader pattern with ghost snares under the
B section, and a six-hit snare roll closing each half. PSID init/play
addresses are `$1000` and `$1080`.

"Dark Armada" (`scripts/generate_imperial_markov_sid.py`,
`src/music/imperial_march.a`) is an original dark 20-bar military cue in G
minor without quoting an existing melody. A deterministic second-order
Markov chain is trained on transitions between eight complete original
motifs, preserving recognizable phrases while generating a new route through
them. Three 83.33 BPM bars establish pulse stabs and a half-time backing beat,
four 93.75 BPM bars reveal fragments of the lead, and twelve 107 BPM bars
deliver the full march. The generated demo/PSID output removes the first eight
seconds and loops the remaining 37.76-second three-voice arrangement, which uses a
saw-to-PWM brass lead, clipped minor/modal arpeggios, and triangle bass
time-shared with pitch-drop kick, double snares, and roll fills. A low
resonant filter sweep darkens the rhythm voice. PSID init/play addresses are
`$1000` and `$1080`.

"Gearshift" (`scripts/generate_gearshift_markov_sid.py`,
`src/music/gearshift_markov.a`) is an original 16-bar C64 game cue at 125 BPM.
A deterministic second-order Markov chain learns transitions among eight
original one-bar hook motifs, with first-order backoff for occasional new
branches. The fixed seed produces a reproducible 15-bar route followed by a
written cadence; the training graph, seed, generated route, and motif data are
saved in `src/music/gearshift_markov_chain.json`. Voice 1 uses a hard-restarted
saw attack and fast-PWM pulse body, voice 2 plays clipped minor-key arpeggios,
and voice 3 time-shares octave pulse bass with pitch-drop kicks, noise snares,
and four turnaround fills. The result is a seamless 30.72-second PAL loop with
PSID init/play addresses at `$1000` and `$1080`.

Sparkle2 support:

- Sparkle2 reference: `https://github.com/spartaomg/Sparkle2`.
- `scripts/ensure_sparkle2.sh` clones or updates `https://github.com/SkiltonUSA/Sparkle2.git` under `.context/Sparkle2` by default; override with `SPARKLE2_REPO` to test another fork.
- `scripts/generate_sparkle_sls.py` writes a Sparkle Loader Script for `build/StarwarsScrollerDemo-sparkle-part.prg`.
- `scripts/build_sparkle.sh` runs the normal build, prepares `build/StarwarsScrollerDemo.sls`, and invokes Sparkle2 through `mono` or `wine` when either is installed.
- Mono is the preferred non-Windows runner. Wine on macOS can launch Sparkle2 but may exit without writing a D64; in that case use the generated `build/StarwarsScrollerDemo.sls` with Sparkle2 on Windows.

Vendored Nobounds assets:

The original Starwars assets come from a fork of Robert Troughton's
`C64Demo-PublicReleases:main`: `https://github.com/SkiltonUSA/C64Demo-PublicReleases`.

- `src/assets/starwars/swcode.prg`
- `src/assets/starwars/font.bin`
- `src/assets/starwars/text.bin`
- `src/assets/starwars/screen.bin`
- `src/assets/starwars/sprites.bin`
- `src/assets/starwars/basecode.prg`
- `src/assets/starwars/music.prg`
- `src/assets/starwars/disk.prg`
