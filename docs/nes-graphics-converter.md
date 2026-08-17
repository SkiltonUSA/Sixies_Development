# NES PNG Graphics Converter

The NES has no general-purpose bitmap framebuffer. Artwork is stored as 8x8,
two-bit CHR tiles, while a nametable selects the tile shown at each position.
`scripts/convert-png-to-nes.py` converts a PNG into that representation without
third-party Python packages.

## Basic use

```sh
python3 scripts/convert-png-to-nes.py input.png ports/nes/build/input
```

The converter writes:

- `input.chr`: NES 2bpp pattern data, padded to 4 KiB by default.
- `input.nam`: compact row-major tile indices for the converted image.
- `input.pal`: four NES palette bytes.
- `input.json`: dimensions, tile count, palette, and conversion settings.
- `input.preview.png`: the exact pixels produced by decoding the generated CHR
  and nametable through the selected palette.

The `.nam` file contains only the tile rectangle required by the image. It is
not automatically expanded to a 32x30 screen nametable or followed by a
64-byte attribute table.

## Controlled conversion

For production artwork, specify the target dimensions and palette rather than
depending on automatic palette selection:

```sh
python3 scripts/convert-png-to-nes.py \
  ports/nes/assets/dice/dice_6_64x64.png \
  ports/nes/build/dice_6 \
  --width 24 --height 24 \
  --palette 0f,00,28,27
```

Useful options include:

- `--dither` applies ordered color dithering before palette mapping.
- `--no-deduplicate` retains duplicate tiles in source order.
- `--chr-size 0` writes only the used CHR bytes instead of padding to 4 KiB.
- `--tile-limit N` fails if conversion exceeds the available tile budget.
- `--alpha-threshold N` controls which source pixels become palette index zero.

## Hardware constraints

One converter invocation uses one four-entry NES background palette. Palette
index zero is also used for transparent source pixels. Full screens that need
multiple palettes must combine converted regions and generate an NES attribute
table at a higher layer; every 16x16-pixel background quadrant can select only
one of four background palettes.

CHR tiles have no alpha channel, antialiasing, or partial opacity. The preview
is therefore the required review artifact. If its silhouette is unclear,
adjust the source pixel art, dimensions, explicit palette, or alpha threshold
rather than relying on the original PNG appearance.

## Inspecting CHR and ROMs

Render a raw CHR bank as a 16-column tile sheet:

```sh
python3 scripts/render-nes-chr.py ports/nes/build/sixies.chr chr-preview.png
```

Render the CHR ROM embedded in an iNES cartridge image:

```sh
python3 scripts/render-nes-chr.py ports/nes/build/sixies-nes.nes rom-chr.png \
  --ines --palette 0f,00,28,27
```

Use `--nametable`, `--tile-columns`, and `--tile-rows` together to reconstruct
a compact tilemap instead of displaying sequential tiles. The shared library
also exposes `map_nametable_to_chr`, `expand_metatile_atlas`, and `parse_ines`
for asset-build scripts.

The inspection and metatile features are informed by Matthew Gilmore's
`fc_tools` utilities. The pinned source and license reference is recorded in
`third_party/segaloco-fc-tools/README.md`; the external C and shell programs
are not build dependencies.
