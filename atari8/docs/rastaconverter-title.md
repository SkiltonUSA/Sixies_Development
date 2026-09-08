# RastaConverter title pipeline

The color title is generated from `assets/title_rasta_source.png` with
[RastaConverter](https://github.com/ilmenit/RastaConverter) 1.0-RC12. The
checked conversion was made at commit
`5fd4d384cc5f8c8584407c67833d640606e7d0d7` as a deterministic, single-frame
NTSC ANTIC-E image. Dual-frame mode is deliberately disabled to avoid temporal
flicker.

The converter's standalone result is 21 KB and occupies `$2000-$7DB4`, which
overlaps Sixies' game code and state on a 64K machine. Sixies therefore keeps
the converter's optimized image but post-processes it into three fixed
playfield colors plus black. The selected gold, purple, and gray preserve the
most important structure without any title DLI. This lets the existing title
music and input code continue to run, removes scanline color flicker, and
reuses the game's 7.75 KB framebuffer.

The start prompt and machine label are written directly into the packed
ANTIC-E bitmap after color reduction. Each glyph pixel occupies a complete
mode-E color pair and two scanlines, keeping the UI text crisp and readable.

## Regeneration on macOS

Install CMake and FreeImage, then build the console-only converter outside the
tracked source tree:

```sh
brew install cmake freeimage
git clone https://github.com/ilmenit/RastaConverter.git .tools/rastaconverter
git -C .tools/rastaconverter checkout 5fd4d384cc5f8c8584407c67833d640606e7d0d7
cmake -S .tools/rastaconverter -B .tools/rastaconverter/build/sixies-headless \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_NO_GUI=ON
cmake --build .tools/rastaconverter/build/sixies-headless --config Release
make -C atari8 title-rasta
make -C atari8 test
```

`make title-rasta` uses one optimizer thread, a fixed seed, box scaling,
source-image scoring, no dithering, and 500,000 evaluations. It writes the inspection preview and the
committed `.mic`/`.pal` inputs consumed by the normal asset build.
