#!/usr/bin/env python3
"""Dependency-free PNG to Nintendo NES graphics conversion primitives."""

import json
import struct
import zlib
from collections import Counter
from dataclasses import dataclass
from itertools import chain
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TILE_SIZE = 8
TILE_BYTES = 16

# A commonly used NTSC approximation. Real console output varies by decoder.
NES_PALETTE = (
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
    (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228),
    (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40),
    (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108),
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
    (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
    (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0),
)


@dataclass(frozen=True)
class RgbaImage:
    width: int
    height: int
    pixels: tuple

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError("image dimensions must be positive")
        if len(self.pixels) != self.height:
            raise ValueError("pixel row count does not match image height")
        if any(len(row) != self.width for row in self.pixels):
            raise ValueError("pixel row width does not match image width")


@dataclass(frozen=True)
class TileSet:
    chr_data: bytes
    nametable: bytes
    tile_columns: int
    tile_rows: int
    tile_count: int


@dataclass(frozen=True)
class InesImage:
    header: bytes
    trainer: bytes
    prg_rom: bytes
    chr_rom: bytes
    trailing_data: bytes


def _paeth(left, up, upper_left):
    estimate = left + up - upper_left
    distances = (
        (abs(estimate - left), left),
        (abs(estimate - up), up),
        (abs(estimate - upper_left), upper_left),
    )
    return min(distances, key=lambda item: item[0])[1]


def _unfilter(raw, width, height, bytes_per_pixel):
    stride = width * bytes_per_pixel
    rows = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        if offset + stride + 1 > len(raw):
            raise ValueError("PNG pixel stream is truncated")
        filter_type = raw[offset]
        scanline = bytearray(raw[offset + 1:offset + stride + 1])
        offset += stride + 1
        for index in range(stride):
            left = scanline[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 1:
                scanline[index] = (scanline[index] + left) & 0xff
            elif filter_type == 2:
                scanline[index] = (scanline[index] + up) & 0xff
            elif filter_type == 3:
                scanline[index] = (scanline[index] + ((left + up) // 2)) & 0xff
            elif filter_type == 4:
                scanline[index] = (scanline[index] + _paeth(left, up, upper_left)) & 0xff
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter {filter_type}")
        rows.append(scanline)
        previous = scanline
    return rows


def read_png(path):
    """Read an 8-bit, non-interlaced grayscale, RGB, indexed, or RGBA PNG."""
    path = Path(path)
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError(f"{path} is not a PNG file")

    offset = 8
    compressed = bytearray()
    header = None
    color_table = None
    transparency = b""
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError(f"{path} has a truncated PNG chunk")
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk_data = data[offset + 8:offset + 8 + length]
        if len(chunk_data) != length:
            raise ValueError(f"{path} has a truncated {chunk_type!r} chunk")
        offset += length + 12
        if chunk_type == b"IHDR":
            header = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == b"PLTE":
            color_table = [tuple(chunk_data[index:index + 3])
                           for index in range(0, len(chunk_data), 3)]
        elif chunk_type == b"tRNS":
            transparency = chunk_data
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if header is None:
        raise ValueError(f"{path} has no IHDR chunk")
    width, height, depth, color_type, compression, filtering, interlace = header
    if depth != 8 or compression != 0 or filtering != 0 or interlace != 0:
        raise ValueError(f"{path} must be non-interlaced 8-bit PNG data")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        raise ValueError(f"{path} uses unsupported PNG color type {color_type}")
    if color_type == 3 and color_table is None:
        raise ValueError(f"{path} is indexed but has no PLTE chunk")

    rows = _unfilter(zlib.decompress(compressed), width, height, channels)
    pixels = []
    for row in rows:
        output = []
        for x in range(width):
            sample = row[x * channels:(x + 1) * channels]
            if color_type == 0:
                output.append((sample[0], sample[0], sample[0], 255))
            elif color_type == 2:
                output.append((sample[0], sample[1], sample[2], 255))
            elif color_type == 3:
                index = sample[0]
                if index >= len(color_table):
                    raise ValueError(f"{path} references missing palette color {index}")
                alpha = transparency[index] if index < len(transparency) else 255
                output.append(color_table[index] + (alpha,))
            elif color_type == 4:
                output.append((sample[0], sample[0], sample[0], sample[1]))
            else:
                output.append(tuple(sample))
        pixels.append(tuple(output))
    return RgbaImage(width, height, tuple(pixels))


def _png_chunk(chunk_type, payload):
    body = chunk_type + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def write_png(path, image):
    """Write an RgbaImage as a non-interlaced 8-bit RGBA PNG."""
    raw = bytearray()
    for row in image.pixels:
        raw.append(0)
        raw.extend(chain.from_iterable(row))
    header = struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0)
    output = bytearray(PNG_SIGNATURE)
    output.extend(_png_chunk(b"IHDR", header))
    output.extend(_png_chunk(b"IDAT", zlib.compress(raw, 9)))
    output.extend(_png_chunk(b"IEND", b""))
    Path(path).write_bytes(output)


def resize_nearest(image, width, height):
    if width <= 0 or height <= 0:
        raise ValueError("resize dimensions must be positive")
    rows = []
    for y in range(height):
        source_y = (2 * y + 1) * image.height // (2 * height)
        rows.append(tuple(
            image.pixels[source_y][(2 * x + 1) * image.width // (2 * width)]
            for x in range(width)
        ))
    return RgbaImage(width, height, tuple(rows))


def color_distance(first, second):
    red = first[0] - second[0]
    green = first[1] - second[1]
    blue = first[2] - second[2]
    return 30 * red * red + 59 * green * green + 11 * blue * blue


def choose_palette(image, background=0x0f, alpha_threshold=96):
    """Choose one NES background palette using weighted greedy error reduction."""
    if not 0 <= background < 64:
        raise ValueError("background palette index must be between 0x00 and 0x3f")
    counts = Counter(
        ((red >> 3) << 3, (green >> 3) << 3, (blue >> 3) << 3)
        for row in image.pixels for red, green, blue, alpha in row
        if alpha >= alpha_threshold
    )
    colors = counts.most_common(256)
    selected = [background]
    candidates = [index for index in range(64) if NES_PALETTE[index] != NES_PALETTE[background]]
    while len(selected) < 4:
        best = min(candidates, key=lambda candidate: sum(
            count * min(color_distance(color, NES_PALETTE[index])
                        for index in selected + [candidate])
            for color, count in colors
        )) if colors else background
        selected.append(best)
        candidates = [index for index in candidates
                      if NES_PALETTE[index] != NES_PALETTE[best]]
        if not candidates:
            candidates = [background]
    return tuple(selected)


def parse_palette(value):
    entries = value.replace("$", "").replace("0x", "").split(",")
    if len(entries) != 4:
        raise ValueError("palette must contain four comma-separated NES hex values")
    palette = tuple(int(entry.strip(), 16) for entry in entries)
    if any(index < 0 or index >= 64 for index in palette):
        raise ValueError("NES palette values must be between 00 and 3f")
    return palette


def quantize(image, palette, alpha_threshold=96, dither=False):
    if len(palette) != 4:
        raise ValueError("an NES palette must contain exactly four colors")
    bayer = ((0, 8, 2, 10), (12, 4, 14, 6),
             (3, 11, 1, 9), (15, 7, 13, 5))
    output = []
    for y, row in enumerate(image.pixels):
        indexed_row = []
        for x, (red, green, blue, alpha) in enumerate(row):
            if alpha < alpha_threshold:
                indexed_row.append(0)
                continue
            adjustment = (bayer[y % 4][x % 4] - 7.5) * 3 if dither else 0
            adjusted = tuple(max(0, min(255, int(channel + adjustment)))
                             for channel in (red, green, blue))
            indexed_row.append(min(range(4), key=lambda index:
                color_distance(adjusted, NES_PALETTE[palette[index]])))
        output.append(tuple(indexed_row))
    return tuple(output)


def encode_tile(pixels):
    if len(pixels) != TILE_SIZE or any(len(row) != TILE_SIZE for row in pixels):
        raise ValueError("NES tiles must be 8x8 pixels")
    plane0 = []
    plane1 = []
    for row in pixels:
        low = 0
        high = 0
        for value in row:
            if not 0 <= value <= 3:
                raise ValueError("NES pixel values must be between 0 and 3")
            low = (low << 1) | (value & 1)
            high = (high << 1) | ((value >> 1) & 1)
        plane0.append(low)
        plane1.append(high)
    return bytes(plane0 + plane1)


def decode_tile(data):
    """Decode one NES 2bpp planar tile into eight rows of palette indices."""
    if len(data) != TILE_BYTES:
        raise ValueError("an NES tile must contain exactly 16 bytes")
    return tuple(tuple(
        ((data[y] >> (7 - x)) & 1) | (((data[y + 8] >> (7 - x)) & 1) << 1)
        for x in range(TILE_SIZE)
    ) for y in range(TILE_SIZE))


def decode_chr(chr_data, max_tiles=None):
    """Decode a CHR byte stream into 8x8 indexed tiles."""
    if len(chr_data) % TILE_BYTES:
        raise ValueError("CHR data length must be a multiple of 16 bytes")
    tile_count = len(chr_data) // TILE_BYTES
    if max_tiles is not None:
        if max_tiles < 0:
            raise ValueError("maximum tile count must not be negative")
        tile_count = min(tile_count, max_tiles)
    return tuple(decode_tile(chr_data[offset:offset + TILE_BYTES])
                 for offset in range(0, tile_count * TILE_BYTES, TILE_BYTES))


def map_nametable_to_chr(chr_data, nametable):
    """Expand tile indices into a contiguous stream of 16-byte CHR tiles."""
    if len(chr_data) % TILE_BYTES:
        raise ValueError("CHR data length must be a multiple of 16 bytes")
    tile_count = len(chr_data) // TILE_BYTES
    output = bytearray()
    for tile_index in nametable:
        if tile_index >= tile_count:
            raise ValueError(f"nametable references missing CHR tile {tile_index}")
        offset = tile_index * TILE_BYTES
        output.extend(chr_data[offset:offset + TILE_BYTES])
    return bytes(output)


def render_tilemap(chr_data, nametable, tile_columns, tile_rows):
    """Render a rectangular nametable using palette indices 0 through 3."""
    if tile_columns <= 0 or tile_rows <= 0:
        raise ValueError("tilemap dimensions must be positive")
    if len(nametable) != tile_columns * tile_rows:
        raise ValueError("nametable size does not match its tile dimensions")
    mapped_tiles = decode_chr(map_nametable_to_chr(chr_data, nametable))
    rows = []
    for tile_y in range(tile_rows):
        for pixel_y in range(TILE_SIZE):
            row = []
            for tile_x in range(tile_columns):
                row.extend(mapped_tiles[tile_y * tile_columns + tile_x][pixel_y])
            rows.append(tuple(row))
    return tuple(rows)


def render_chr_sheet(chr_data, columns=16, max_tiles=None):
    """Render sequential CHR tiles as an indexed tile sheet."""
    if columns <= 0:
        raise ValueError("tile sheet columns must be positive")
    tiles = decode_chr(chr_data, max_tiles)
    if not tiles:
        raise ValueError("CHR data contains no tiles")
    tile_rows = (len(tiles) + columns - 1) // columns
    rows = []
    blank = (0,) * TILE_SIZE
    for tile_y in range(tile_rows):
        for pixel_y in range(TILE_SIZE):
            row = []
            for tile_x in range(columns):
                tile_index = tile_y * columns + tile_x
                row.extend(tiles[tile_index][pixel_y]
                           if tile_index < len(tiles) else blank)
            rows.append(tuple(row))
    return tuple(rows)


def crop_indexed(indexed, width, height):
    if width <= 0 or height <= 0:
        raise ValueError("crop dimensions must be positive")
    if height > len(indexed) or any(width > len(row) for row in indexed[:height]):
        raise ValueError("crop exceeds indexed image dimensions")
    return tuple(tuple(row[:width]) for row in indexed[:height])


def expand_metatile_atlas(definitions, metatile_width, metatile_height,
                          columns=16, tile_count=None, packed=True,
                          row_major=True):
    """Expand metatile definitions into a row-major tilemap atlas.

    Packed data stores all cells of each metatile together. Unpacked data
    stores one cell plane for every metatile. Cell order can be row-major or
    column-major within each metatile.
    """
    if metatile_width <= 0 or metatile_height <= 0 or columns <= 0:
        raise ValueError("metatile dimensions and atlas columns must be positive")
    area = metatile_width * metatile_height
    if tile_count is None:
        if len(definitions) % area:
            raise ValueError("metatile data length is not divisible by its area")
        tile_count = len(definitions) // area
    if tile_count <= 0 or len(definitions) != tile_count * area:
        raise ValueError("metatile data length does not match tile count")

    atlas_rows = (tile_count + columns - 1) // columns
    output = bytearray()
    for atlas_y in range(atlas_rows * metatile_height):
        local_y = atlas_y % metatile_height
        metatile_y = atlas_y // metatile_height
        for atlas_x in range(columns * metatile_width):
            local_x = atlas_x % metatile_width
            metatile_x = atlas_x // metatile_width
            metatile_index = metatile_y * columns + metatile_x
            if metatile_index >= tile_count:
                output.append(0)
                continue
            cell = (local_y * metatile_width + local_x if row_major
                    else local_x * metatile_height + local_y)
            source = (metatile_index * area + cell if packed
                      else cell * tile_count + metatile_index)
            output.append(definitions[source])
    return bytes(output)


def parse_ines(data):
    """Split an iNES ROM into header, trainer, PRG ROM, CHR ROM, and trailing data."""
    if len(data) < 16 or data[:4] != b"NES\x1a":
        raise ValueError("file does not contain an iNES header")
    header = data[:16]
    trainer_size = 512 if header[6] & 0x04 else 0
    prg_size = header[4] * 16384
    chr_size = header[5] * 8192
    required = 16 + trainer_size + prg_size + chr_size
    if len(data) < required:
        raise ValueError("iNES ROM is truncated")
    offset = 16
    trainer = data[offset:offset + trainer_size]
    offset += trainer_size
    prg_rom = data[offset:offset + prg_size]
    offset += prg_size
    chr_rom = data[offset:offset + chr_size]
    offset += chr_size
    return InesImage(header, trainer, prg_rom, chr_rom, data[offset:])


def build_tiles(indexed, deduplicate=True, tile_limit=256):
    height = len(indexed)
    width = len(indexed[0]) if height else 0
    if width == 0 or any(len(row) != width for row in indexed):
        raise ValueError("indexed image must be a non-empty rectangle")
    tile_columns = (width + 7) // 8
    tile_rows = (height + 7) // 8
    tiles = []
    tile_indices = {}
    nametable = bytearray()
    for tile_y in range(tile_rows):
        for tile_x in range(tile_columns):
            pixels = []
            for y in range(8):
                source_y = tile_y * 8 + y
                pixels.append(tuple(
                    indexed[source_y][tile_x * 8 + x]
                    if source_y < height and tile_x * 8 + x < width else 0
                    for x in range(8)
                ))
            encoded = encode_tile(pixels)
            if deduplicate and encoded in tile_indices:
                tile_index = tile_indices[encoded]
            else:
                tile_index = len(tiles)
                if tile_index >= tile_limit or tile_index >= 256:
                    raise ValueError(f"graphics require more than {min(tile_limit, 256)} tiles")
                tiles.append(encoded)
                tile_indices[encoded] = tile_index
            nametable.append(tile_index)
    return TileSet(b"".join(tiles), bytes(nametable), tile_columns, tile_rows, len(tiles))


def indexed_preview(indexed, palette):
    rows = tuple(tuple(NES_PALETTE[palette[value]] + (255,) for value in row)
                 for row in indexed)
    return RgbaImage(len(rows[0]), len(rows), rows)


def convert_png(input_path, output_prefix, width=None, height=None, palette=None,
                background=0x0f, alpha_threshold=96, dither=False,
                deduplicate=True, tile_limit=256, chr_size=4096):
    input_path = Path(input_path)
    output_prefix = Path(output_prefix)
    image = read_png(input_path)
    if (width is None) != (height is None):
        raise ValueError("width and height must be supplied together")
    if width is not None:
        image = resize_nearest(image, width, height)
    if palette is None:
        palette = choose_palette(image, background, alpha_threshold)
    indexed = quantize(image, palette, alpha_threshold, dither)
    tiles = build_tiles(indexed, deduplicate, tile_limit)
    chr_data = tiles.chr_data
    if chr_size:
        if len(chr_data) > chr_size:
            raise ValueError(f"CHR data is {len(chr_data)} bytes; limit is {chr_size}")
        chr_data += bytes(chr_size - len(chr_data))

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    paths = {
        "chr": output_prefix.with_suffix(".chr"),
        "nametable": output_prefix.with_suffix(".nam"),
        "palette": output_prefix.with_suffix(".pal"),
        "metadata": output_prefix.with_suffix(".json"),
        "preview": output_prefix.with_suffix(".preview.png"),
    }
    paths["chr"].write_bytes(chr_data)
    paths["nametable"].write_bytes(tiles.nametable)
    paths["palette"].write_bytes(bytes(palette))
    decoded = render_tilemap(
        tiles.chr_data, tiles.nametable, tiles.tile_columns, tiles.tile_rows
    )
    decoded = crop_indexed(decoded, image.width, image.height)
    write_png(paths["preview"], indexed_preview(decoded, palette))
    metadata = {
        "source": str(input_path),
        "pixel_width": image.width,
        "pixel_height": image.height,
        "tile_columns": tiles.tile_columns,
        "tile_rows": tiles.tile_rows,
        "unique_tiles": tiles.tile_count,
        "palette": [f"{value:02x}" for value in palette],
        "chr_bytes": len(chr_data),
        "nametable_bytes": len(tiles.nametable),
        "deduplicated": deduplicate,
        "dithered": dither,
        "preview_source": "decoded_chr_and_nametable",
    }
    paths["metadata"].write_text(json.dumps(metadata, indent=2) + "\n")
    return paths, metadata
