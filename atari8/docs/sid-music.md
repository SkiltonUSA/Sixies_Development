# Converting SID music to Atari POKEY

Sixies uses a native POKEY conversion of **“Eternity #1 (intro)”** by
Przemysław Lewandowski (Sonix) for its title screen. The shipping conversion is
made with Ivo van Poorten's `sid2sapr` from `saprtools`.

## Why conversion is necessary

A `.sid` file contains 6502 player code that writes the C64 SID registers. SID
has hardware ADSR envelopes, pulse-width modulation, filters, and waveforms
that POKEY does not reproduce register-for-register. `sid2sapr` runs the SID
player offline and translates its musical state into native POKEY frequency,
distortion, and volume register frames.

## Shipping conversion

The development setup pins `saprtools` and builds both `sid2sapr` and its LZSS
compressor under `.tools/atari8`. Regenerate the committed title stream with:

```sh
make -C atari8 setup-tools
make -C atari8 music-sapr
```

The target performs the equivalent of:

```sh
sid2sapr -b softbass -a -p 9 -n 961 \
  -o eternity_1_intro_softbass.sapr Eternity_1_intro.sid
lzss -6 eternity_1_intro_softbass.sapr \
  eternity_1_intro_softbass.lz16
```

The raw 961-frame SAP-R stream is 8,649 bytes. LZSS reduces this particular
tune to 399 bytes in `assets/music/eternity_1_intro_softbass.lz16`.

`-b softbass` uses POKEY timer IRQs to synthesize bass notes below the normal
8-bit divider range. `-a` adjusts mono note cancellation, while `-p 9` keeps
the mixed volume under control.

## Game player

`src/sid_music.s` is a ca65 adaptation of the LZSS softbass player distributed
with `saprtools`. It provides `sid_music_start`, `sid_music_tick`, and
`sid_music_stop` for `src/sound.s`.

The title tune occupies all required POKEY channels, which is safe because
gameplay effects do not begin until the title music is stopped. The player:

- advances five out of every six NTSC frames to preserve the SID's 50 Hz PAL
  tempo;
- keeps nine 256-byte LZSS history pages and three aligned softbass wave pages
  in non-file-backed high RAM;
- enables only the three softbass timer IRQ sources during title playback and
  polls POKEY's keyboard matrix directly, preventing nested OS/timer IRQ stack
  growth during the repeating attract screens;
- restores the original IRQ vector and POKEY mask before instructions and
  gameplay; and
- restarts the tune if the title screen remains open through all 961 frames.

The conversion and register stream are BSD-2-Clause work by Ivo van Poorten.
The LZSS player design is MIT-licensed work by DMSC, adapted for `saprtools` by
Ivo van Poorten and ported here to ca65.

## Legacy comparison converter

`scripts/sid_to_pokey.py` and `make music` retain the earlier Sixies converter
for comparison and WAV previews. It maps three SID voices directly to POKEY
channels 1–3 and reserves channel 4 for effects, but it does not provide the
new softbass sound and its uncompressed stream is much larger. It is no longer
included by the game build.
