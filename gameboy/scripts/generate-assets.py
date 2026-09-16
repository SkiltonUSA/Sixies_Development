#!/usr/bin/env python3

from pathlib import Path
import colorsys
import re

from PIL import Image, ImageChops, ImageDraw

from dice_shading import FACE_SHADES, save_shading_previews, shade_die


ROOT = Path(__file__).resolve().parents[2]
GAMEBOY = ROOT / "gameboy"
ATARI = ROOT / "atari8"
APPLE = ROOT / "apple2" / "assets"

FONT_GLYPH_ORDER = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+!:"
CREDITS_FONT_GLYPH_ORDER = FONT_GLYPH_ORDER + ".()"
FONT_PRIMARY = (224, 248, 207)

GRID_PALETTE = (
    (13, 56, 0),
    (48, 98, 48),
    (139, 172, 15),
    (202, 220, 159),
)

GRID_DISPLAY_PALETTE = (
    (229, 240, 183),
    (139, 172, 15),
    (48, 98, 48),
    (13, 56, 0),
)

CALLOUT_DISPLAY_PALETTE = (
    (0, 0, 0, 0),
    (229, 240, 183, 255),
    (120, 72, 172, 255),
    (13, 56, 0, 255),
)

CALLOUTS = (
    "awesome", "boom", "dang", "fives", "lets_go",
    "sixies", "whoa", "wow", "yeah", "yes",
)

CALLOUT_SPRITE_WIDTH = 8
CALLOUT_SPRITE_HEIGHT = 2

CALLOUT_TEMPLATES = {
    "awesome": "awesome",
    "boom": "yay_a",
    "dang": "dang",
    "fives": "fives",
    "lets_go": "lets_go",
    "sixies": "yay_b",
    "whoa": "whoa",
    "wow": "wow",
    "yeah": "yeah",
    "yes": "yes",
}

def image_mask(path, size, threshold=96):
    with Image.open(path) as source:
        rgb = source.convert("RGB")
    intensity = ImageChops.lighter(
        ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
        rgb.getchannel("B"),
    )
    bounds = intensity.point(lambda value: 255 if value >= 16 else 0).getbbox()
    if bounds is None:
        raise ValueError(f"no visible art in {path}")
    detail = intensity.crop(bounds)
    detail.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("L", size, 0)
    canvas.paste(detail, ((size[0] - detail.width) // 2, (size[1] - detail.height) // 2))
    return canvas.point(lambda value: 3 if value >= threshold else 0)


def logo_wordmark(size):
    source_palette = GRID_PALETTE
    with Image.open(GAMEBOY / "assets" / "logo_master.png") as source:
        source = source.convert("RGB").crop((2, 58, 158, 122)).resize(size, Image.Resampling.LANCZOS)
    result = Image.new("L", size)
    for y in range(size[1]):
        for x in range(size[0]):
            color = source.getpixel((x, y))
            result.putpixel(
                (x, y),
                min(
                    range(4),
                    key=lambda index: sum((color[channel] - source_palette[index][channel]) ** 2 for channel in range(3)),
                ),
            )
    return result


def game_logo_wordmark(size):
    with Image.open(GAMEBOY / "assets" / "game_logo_master.png") as master:
        source = master.convert("RGB").crop((28, 55, 1983, 717)).resize(size, Image.Resampling.LANCZOS)
    result = Image.new("L", size)
    for y in range(size[1]):
        for x in range(size[0]):
            color = source.getpixel((x, y))
            result.putpixel(
                (x, y),
                min(
                    range(4),
                    key=lambda index: sum((color[channel] - GRID_PALETTE[index][channel]) ** 2 for channel in range(3)),
                ),
            )
    return result


def lanky_glyphs():
    with Image.open(GAMEBOY / "assets" / "font_lanky_master.png") as master:
        source = master.convert("RGB")
    if source.size != (128, 112):
        raise ValueError(f"expected 128x112 Lanky font atlas, got {source.size}")
    glyphs = {}
    for codepoint in range(32, 127):
        index = codepoint - 32
        tile = source.crop((index % 16 * 8, index // 16 * 8, index % 16 * 8 + 8, index // 16 * 8 + 8))
        mask = Image.new("L", (8, 8), 0)
        mask.putdata([3 if pixel in ((0, 0, 0), (7, 24, 33)) else 0 for pixel in tile.getdata()])
        bounds = mask.getbbox()
        glyphs[chr(codepoint)] = mask.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (2, 8), 0)
    return glyphs


def lanky_text(image, text, left, top, glyphs, shade=3):
    width = sum(glyphs[character].width + 1 for character in text) - 1
    if left < 0 or left + width > image.width or top + 8 > image.height:
        raise ValueError(f"Lanky text does not fit: {text} at {left}, {top}")
    for character in text:
        glyph = glyphs[character]
        image.paste(shade, (left, top, left + glyph.width, top + 8), glyph.point(lambda value: 255 if value else 0))
        left += glyph.width + 1


def make_font_tiles(glyph_order=FONT_GLYPH_ORDER):
    master_path = GAMEBOY / "assets" / "font_itty_bitty_master.png"
    with Image.open(master_path) as master:
        if master.size != (128, 112):
            raise ValueError(f"expected 128x112 font atlas, got {master.size}: {master_path}")
        source = master.convert("RGB")

    tiles = []
    for glyph in glyph_order:
        codepoint = ord(glyph) - 32
        left = (codepoint & 15) * 8
        top = (codepoint >> 4) * 8
        source_tile = source.crop((left, top, left + 8, top + 8))
        tile = Image.new("L", (8, 8), 0)
        for y in range(8):
            for x in range(8):
                color = source_tile.getpixel((x, y))
                if color == FONT_PRIMARY:
                    tile.putpixel((x, y), 3)
        tiles.append(tile)
    return tiles


def make_title_prompt():
    with Image.open(GAMEBOY / "assets" / "fonts" / "morbidosa" / "Morbidosa_avr.bmp") as master:
        if master.size != (128, 128):
            raise ValueError(f"expected 128x128 Morbidosa atlas, got {master.size}")
        atlas = master.convert("L").point(lambda value: 3 if value else 0)
    phrase = "Press Start"
    prompt = Image.new("L", (len(phrase) * 8, 8), 0)
    for index, character in enumerate(phrase):
        if character == " ":
            continue
        codepoint = ord(character) - 32 + 128
        left = (codepoint % 16) * 8
        top = (codepoint // 16) * 8
        glyph = atlas.crop((left, top, left + 8, top + 8))
        bounds = glyph.getbbox()
        if bounds is None:
            raise ValueError(f"missing Morbidosa glyph: {character}")
        prompt.paste(glyph, (index * 8, 0))
    if len(phrase.replace(" ", "")) > 10:
        raise ValueError("title prompt exceeds ten sprites per scanline")
    return prompt


def make_morbidosa_tiles(glyph_order):
    with Image.open(GAMEBOY / "assets" / "fonts" / "morbidosa" / "Morbidosa_avr.bmp") as master:
        atlas = master.convert("L").point(lambda value: 3 if value else 0)

    tiles = []
    for character in glyph_order:
        if character == " ":
            tiles.append(Image.new("L", (8, 8), 0))
            continue
        codepoint = ord(character) - 32 + 128
        left = (codepoint % 16) * 8
        top = (codepoint // 16) * 8
        glyph = atlas.crop((left, top, left + 8, top + 8))
        if not glyph.getbbox():
            raise ValueError(f"missing Morbidosa glyph: {character}")
        tiles.append(glyph)
    return tiles


def parse_sprite(path, width, height):
    values = [
        int(value, 16)
        for value in re.findall(r"\$([0-9a-fA-F]{2})(?![0-9a-fA-F])", path.read_text())
    ]
    bytes_per_row = (width + 7) // 8
    if len(values) < bytes_per_row * height:
        raise ValueError(f"not enough sprite bytes in {path}")
    image = Image.new("L", (width, height), 0)
    pixels = image.load()
    for y in range(height):
        row = values[y * bytes_per_row:(y + 1) * bytes_per_row]
        for x in range(width):
            if row[x // 8] & (0x80 >> (x & 7)):
                pixels[x, y] = 3
    return image


def make_die(source):
    if source.size not in ((16, 16), (18, 18)):
        raise ValueError(f"expected 16x16 or 18x18 die, got {source.size}")
    image = Image.new("L", source.size, 0)
    for y in range(source.height):
        for x in range(source.width):
            color = source.getpixel((x, y))
            if color[3] < 128:
                image.putpixel((x, y), 0)
                continue
            image.putpixel(
                (x, y),
                min(
                    range(4),
                    key=lambda index: sum((color[channel] - GRID_DISPLAY_PALETTE[index][channel]) ** 2 for channel in range(3)),
                ),
            )
    return image


def grid_source():
    master_path = GAMEBOY / "assets" / "grid_layout_master.png"
    with Image.open(master_path) as master:
        if master.size != (167, 144):
            raise ValueError(f"expected 167x144 grid art, got {master.size}: {master_path}")
        return master.convert("RGB")


def grid_shades(source, palette=GRID_DISPLAY_PALETTE):
    image = Image.new("L", source.size)
    image.putdata([
        min(range(4), key=lambda index: sum(
            (color[channel] - palette[index][channel]) ** 2
            for channel in range(3)
        )) for color in source.getdata()
    ])
    return image


def make_cell(highlight):
    source = grid_source()
    vertical = grid_shades(source.crop((29, 30, 30, 31))).getpixel((0, 0))
    horizontal = grid_shades(source.crop((37, 40, 38, 41))).getpixel((0, 0))
    image = Image.new("L", (20, 20), 0)
    draw = ImageDraw.Draw(image)
    draw.line((0, 0, 0, 19), fill=vertical)
    draw.line((0, 0, 19, 0), fill=horizontal)
    draw.line((19, 0, 19, 19), fill=1)
    draw.line((0, 19, 19, 19), fill=1)
    if highlight:
        draw.rectangle((1, 1, 18, 18), fill=3)
    return image


def make_next_panel():
    source = grid_source()
    frame = source.crop((110, 78, 159, 122))
    image = Image.new("RGB", (48, 56), GRID_DISPLAY_PALETTE[0])
    rows = ((0, 8, 8, 16), (20, 21, 16, 48), (36, 44, 48, 56))
    columns = ((0, 8, 0, 8), (24, 25, 8, 40), (41, 49, 40, 48))
    for row, (top, bottom, target_top, target_bottom) in enumerate(rows):
        for column, (left, right, target_left, target_right) in enumerate(columns):
            if row == 1 and column == 1:
                continue
            region = frame.crop((left, top, right, bottom)).resize(
                (target_right - target_left, target_bottom - target_top), Image.Resampling.NEAREST,
            )
            image.paste(region, (target_left, target_top))
    original = grid_shades(image).crop((0, 8, 48, 56))
    panel = Image.new("L", (48, 56), 0)
    sections = ((0, 8, 0, 6), (8, 40, 6, 42), (40, 48, 42, 48))
    for top, bottom, target_top, target_bottom in sections:
        for left, right, target_left, target_right in sections:
            region = original.crop((left, top, right, bottom)).resize(
                (target_right - target_left, target_bottom - target_top), Image.Resampling.NEAREST,
            )
            panel.paste(region, (target_left, target_top + 8))
    return panel


def make_floor():
    with Image.open(GAMEBOY / "assets" / "floor_master.png") as master:
        source = master.convert("RGB")
    if source.size != (2172, 724):
        raise ValueError(f"expected 2172x724 floor art, got {source.size}")
    source = source.crop((711, 424, 1461, 600)).resize((80, 16), Image.Resampling.LANCZOS)
    image = Image.new("L", source.size, 0)
    for y in range(source.height):
        for x in range(source.width):
            color = source.getpixel((x, y))
            image.putpixel(
                (x, y),
                min(
                    range(4),
                    key=lambda index: sum((color[channel] - GRID_PALETTE[index][channel]) ** 2 for channel in range(3)),
                ),
            )
    return image


def make_mascot():
    with Image.open(GAMEBOY / "assets" / "mascot_walk_master.png") as master:
        source = master.convert("RGB")
    if source.size != (2172, 724):
        raise ValueError(f"expected 2172x724 mascot sheet, got {source.size}")
    frames = []
    for frame_index in range(10):
        left = round(frame_index * source.width / 10)
        right = round((frame_index + 1) * source.width / 10)
        frame_source = source.crop((left, 0, right, source.height))
        intensity = ImageChops.lighter(
            ImageChops.lighter(frame_source.getchannel("R"), frame_source.getchannel("G")),
            frame_source.getchannel("B"),
        )
        bounds = intensity.point(lambda value: 255 if value >= 24 else 0).getbbox()
        if bounds is None:
            raise ValueError(f"mascot frame {frame_index} has no visible pixels")
        detail = frame_source.crop(bounds)
        detail.thumbnail((46, 62), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (48, 64), (0, 0, 0))
        canvas.paste(detail, ((48 - detail.width) // 2, 63 - detail.height))
        pixels = canvas.load()
        background = set()
        pending = []
        for x in range(canvas.width):
            for y in (0, canvas.height - 1):
                if max(pixels[x, y]) < 36:
                    background.add((x, y))
                    pending.append((x, y))
        for y in range(canvas.height):
            for x in (0, canvas.width - 1):
                if max(pixels[x, y]) < 36:
                    background.add((x, y))
                    pending.append((x, y))
        while pending:
            x, y = pending.pop()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                neighbor_x, neighbor_y = neighbor
                if 0 <= neighbor_x < canvas.width and 0 <= neighbor_y < canvas.height and neighbor not in background:
                    if max(pixels[neighbor_x, neighbor_y]) < 36:
                        background.add(neighbor)
                        pending.append(neighbor)
        frame = Image.new("L", canvas.size, 0)
        foreground = []
        for y in range(canvas.height):
            for x in range(canvas.width):
                if (x, y) not in background:
                    color = pixels[x, y]
                    frame.putpixel((x, y), 3 if min(color) > 175 else 2 if max(color) > 55 else 1)
                    foreground.append((x, y))
        for x, y in foreground:
            for outline_x in range(max(0, x - 1), min(canvas.width, x + 2)):
                for outline_y in range(max(0, y - 1), min(canvas.height, y + 2)):
                    if frame.getpixel((outline_x, outline_y)) == 0:
                        frame.putpixel((outline_x, outline_y), 1)
        frames.append(frame)
    return frames


def make_credits_logo():
    with Image.open(GAMEBOY / "assets" / "credits_logo_master.png") as master:
        source = master.convert("RGBA")
    visible = source.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    bounds = visible.getbbox()
    if bounds is None:
        raise ValueError("credits logo has no visible pixels")
    logo = source.crop(bounds).resize((144, 56), Image.Resampling.LANCZOS)
    indexed = Image.new("L", logo.size, 255)
    for y in range(logo.height):
        for x in range(logo.width):
            color = logo.getpixel((x, y))
            if color[3] >= 128:
                indexed.putpixel(
                    (x, y),
                    min(
                        range(4),
                        key=lambda index: sum((color[channel] - CREDITS_PALETTE[index][channel]) ** 2 for channel in range(3)),
                    ),
                )
    background = set()
    pending = []
    for x in range(logo.width):
        for y in (0, logo.height - 1):
            if indexed.getpixel((x, y)) in (3, 255):
                background.add((x, y))
                pending.append((x, y))
    for y in range(logo.height):
        for x in (0, logo.width - 1):
            if indexed.getpixel((x, y)) in (3, 255):
                background.add((x, y))
                pending.append((x, y))
    while pending:
        x, y = pending.pop()
        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            neighbor_x, neighbor_y = neighbor
            if 0 <= neighbor_x < logo.width and 0 <= neighbor_y < logo.height and neighbor not in background:
                if indexed.getpixel(neighbor) in (3, 255):
                    background.add(neighbor)
                    pending.append(neighbor)
    image = Image.new("RGB", (160, 72), GRID_PALETTE[0])
    for y in range(logo.height):
        for x in range(logo.width):
            palette_index = indexed.getpixel((x, y))
            if (x, y) not in background and palette_index != 255:
                image.putpixel((x + 8, y), CREDITS_PALETTE[palette_index])
    return image


def itty_glyphs(characters):
    with Image.open(GAMEBOY / "assets" / "font_itty_bitty_master.png") as master:
        source = master.convert("RGB")

    glyphs = {}
    for character in characters:
        codepoint = ord(character) - 32
        if not 0 <= codepoint < 224:
            raise ValueError(f"Itty Bitty does not contain {character!r}")
        left = (codepoint & 15) * 8
        top = (codepoint >> 4) * 8
        source_tile = source.crop((left, top, left + 8, top + 8))
        glyph = Image.new("L", (8, 8), 0)
        for y in range(8):
            for x in range(8):
                if source_tile.getpixel((x, y)) == FONT_PRIMARY:
                    glyph.putpixel((x, y), 1)
        bounds = glyph.getbbox()
        glyphs[character] = glyph.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (3, 8), 0)
    return glyphs


def itty_centered_text(image, text, top, glyphs, shade=0):
    width = sum(glyphs[character].width + 1 for character in text) - 1
    left = (image.width - width) // 2
    for character in text:
        glyph = glyphs[character]
        image.paste(shade, (left, top, left + glyph.width, top + 8), glyph.point(lambda value: 255 if value else 0))
        left += glyph.width + 1


def make_credits_card():
    with Image.open(GAMEBOY / "assets" / "credits_master.png") as master:
        card = master.convert("RGB").resize((160, 144), Image.Resampling.LANCZOS)
    label = Image.new("L", (56, 8), 0)
    for index, glyph in enumerate(make_morbidosa_tiles("CREDITS")):
        label.paste(glyph, (index * 8, 0))
    card.paste(CREDITS_PALETTE[0], (52, 16), label.point(lambda value: 255 if value else 0))
    return card


def callout_source(path):
    with Image.open(path) as master:
        source = master.convert("RGBA")

    pixels = source.load()
    pending = []
    for x in range(source.width):
        pending.extend(((x, 0), (x, source.height - 1)))
    for y in range(1, source.height - 1):
        pending.extend(((0, y), (source.width - 1, y)))
    transparent = set()
    while pending:
        x, y = pending.pop()
        if (x, y) in transparent or max(pixels[x, y][:3]) > 24:
            continue
        transparent.add((x, y))
        for neighbor_x, neighbor_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= neighbor_x < source.width and 0 <= neighbor_y < source.height:
                pending.append((neighbor_x, neighbor_y))
    for x, y in transparent:
        pixels[x, y] = (0, 0, 0, 0)

    bounds = source.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"callout has no visible artwork: {path}")
    return source.crop(bounds)


def callout_canvas(path):
    source = callout_source(path)
    source.thumbnail((64, 32), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (64, 32))
    canvas.alpha_composite(source, ((64 - source.width) // 2, (32 - source.height) // 2))
    return canvas


def make_callout(path):
    canvas = callout_canvas(path)
    image = Image.new("L", canvas.size, 0)
    for y in range(canvas.height):
        for x in range(canvas.width):
            red, green, blue, alpha = canvas.getpixel((x, y))
            if alpha < 96:
                continue
            if red > 176 and green > 176 and blue > 176:
                shade = 1
            elif blue > green + 24 and red > green + 12:
                shade = 2
            else:
                shade = 3
            image.putpixel((x, y), shade)
    return image


def chain_reaction_source(path):
    with Image.open(path) as master:
        source = master.convert("RGBA")

    pixels = source.load()
    pending = []
    for x in range(source.width):
        pending.extend(((x, 0), (x, source.height - 1)))
    for y in range(1, source.height - 1):
        pending.extend(((0, y), (source.width - 1, y)))
    transparent = set()
    while pending:
        x, y = pending.pop()
        red, green, blue, alpha = pixels[x, y]
        if (x, y) in transparent or alpha < 128 or min(red, green, blue) < 220 or max(red, green, blue) - min(red, green, blue) > 12:
            continue
        transparent.add((x, y))
        for neighbor_x, neighbor_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= neighbor_x < source.width and 0 <= neighbor_y < source.height:
                pending.append((neighbor_x, neighbor_y))
    for x, y in transparent:
        pixels[x, y] = (0, 0, 0, 0)

    bounds = source.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"chain reaction has no visible artwork: {path}")
    return source.crop(bounds)


def make_chain_reaction_sprite(path):
    source = chain_reaction_source(path)
    source.thumbnail((64, 32), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (64, 32))
    canvas.alpha_composite(source, ((64 - source.width) // 2, (32 - source.height) // 2))
    image = Image.new("L", canvas.size, 0)
    for y in range(canvas.height):
        for x in range(canvas.width):
            red, green, blue, alpha = canvas.getpixel((x, y))
            if alpha < 96:
                continue
            if red > 176 and green > 176 and blue > 176:
                shade = 1
            elif max(red, green, blue) < 96:
                shade = 3
            else:
                shade = 2
            image.putpixel((x, y), shade)
    return image


CHAIN_STAR_PALETTES = (
    ((0, 0, 0), (229, 240, 183), (95, 125, 23), (13, 56, 0)),
    ((0, 0, 0), (229, 240, 183), (57, 100, 26), (13, 56, 0)),
)


def make_chain_stars(path):
    with Image.open(path) as master:
        source = master.convert("RGBA")
    stars = []
    for variant, palette in enumerate(CHAIN_STAR_PALETTES):
        half = source.crop((variant * source.width // 2, 0, (variant + 1) * source.width // 2, source.height))
        bounds = half.getchannel("A").point(lambda alpha: 255 if alpha >= 128 else 0).getbbox()
        if bounds is None:
            raise ValueError(f"missing chain star {variant}: {path}")
        content = half.crop(bounds)
        content.thumbnail((16, 16), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (16, 16))
        canvas.paste(content, ((16 - content.width) // 2, (16 - content.height) // 2))
        star = Image.new("L", (16, 16), 0)
        for row in range(16):
            for column in range(16):
                color = canvas.getpixel((column, row))
                if color[3] >= 128:
                    shade = min(range(1, 4), key=lambda index: sum((color[channel] - palette[index][channel]) ** 2 for channel in range(3)))
                    star.putpixel((column, row), shade)
        stars.append(star)
    return stars


def make_dmg_chain_star(star):
    compact = Image.new("L", (8, 8), 0)
    for row in range(8):
        for column in range(8):
            if any(star.getpixel((column * 2 + offset_x, row * 2 + offset_y))
                   for offset_y in range(2) for offset_x in range(2)):
                compact.putpixel((column, row), 3)
    return compact


def make_game_mascot(path):
    with Image.open(path) as master:
        source = master.convert("RGBA")
    if source.size != (35, 33):
        raise ValueError(f"expected 35x33 happy mascot, got {source.size}: {path}")

    pixels = source.load()
    pending = []
    for x in range(source.width):
        pending.extend(((x, 0), (x, source.height - 1)))
    for y in range(1, source.height - 1):
        pending.extend(((0, y), (source.width - 1, y)))
    transparent = set()
    while pending:
        x, y = pending.pop()
        red, green, blue, alpha = pixels[x, y]
        is_matte = alpha < 128 or (red >= 190 and green >= 210 and blue >= 140 and green - red <= 18 and red - blue >= 25)
        if (x, y) in transparent or not is_matte:
            continue
        transparent.add((x, y))
        for neighbor_x, neighbor_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= neighbor_x < source.width and 0 <= neighbor_y < source.height:
                pending.append((neighbor_x, neighbor_y))
    for x, y in transparent:
        pixels[x, y] = (0, 0, 0, 0)

    canvas = Image.new("RGBA", (40, 48))
    canvas.alpha_composite(source, (2, 0))
    palette = ((13, 56, 0), (139, 172, 15), (229, 240, 183))
    image = Image.new("L", canvas.size, 0)
    for y in range(canvas.height):
        for x in range(canvas.width):
            red, green, blue, alpha = canvas.getpixel((x, y))
            if alpha >= 128:
                image.putpixel(
                    (x, y),
                    1 + min(range(3), key=lambda index: (red - palette[index][0]) ** 2 + (green - palette[index][1]) ** 2 + (blue - palette[index][2]) ** 2),
                )
    return image


def make_chain():
    path = ATARI / "assets" / "chain_reaction_master.png"
    with Image.open(path) as source:
        rgb = source.convert("RGB")
    intensity = ImageChops.lighter(
        ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
        rgb.getchannel("B"),
    )
    white = intensity.point(lambda value: 255 if value >= 200 else 0)
    chain_letters = (
        ((410, 294, 560, 506), 9), ((568, 278, 718, 480), 9),
        ((718, 266, 874, 456), 9), ((888, 250, 960, 438), 5),
        ((962, 222, 1152, 436), 10),
    )
    reaction_letters = (
        ((186, 632, 348, 842), 8), ((356, 614, 470, 812), 7),
        ((486, 608, 632, 790), 8), ((634, 598, 768, 782), 8),
        ((776, 594, 902, 772), 8), ((910, 590, 976, 766), 4),
        ((984, 590, 1124, 768), 8), ((1134, 574, 1284, 762), 8),
        ((1292, 528, 1396, 760), 5),
    )

    def word(letters, height):
        width = sum(target for _, target in letters) + len(letters) - 1
        result = Image.new("L", (width, height), 0)
        x = 0
        for box, target in letters:
            glyph = white.crop(box).resize((target, height), Image.Resampling.LANCZOS)
            result.paste(glyph.point(lambda value: 3 if value >= 96 else 0), (x, 0))
            x += target + 1
        return result

    full = Image.new("L", (80, 32), 0)
    top = word(chain_letters, 14)
    bottom = word(reaction_letters, 15)
    full.paste(top, ((80 - top.width) // 2, 1))
    full.paste(bottom, ((80 - bottom.width) // 2, 16))
    return full.resize((48, 16), Image.Resampling.NEAREST)


def make_star():
    particle = Image.new("L", (8, 8), 0)
    particle.putpixel((4, 4), 3)
    return particle


def split_tiles(image):
    if image.width % 8 or image.height % 8:
        raise ValueError(f"image is not tile aligned: {image.size}")
    return [
        image.crop((x, y, x + 8, y + 8))
        for y in range(0, image.height, 8)
        for x in range(0, image.width, 8)
    ]


def pack_tiles(tiles):
    output = bytearray()
    for tile in tiles:
        pixels = tile.load()
        for y in range(8):
            low = 0
            high = 0
            for x in range(8):
                value = pixels[x, y] & 3
                low |= (value & 1) << (7 - x)
                high |= ((value >> 1) & 1) << (7 - x)
            output.extend((low, high))
    return output


def c_array(name, data):
    rows = []
    for offset in range(0, len(data), 16):
        rows.append("    " + ", ".join(f"0x{value:02X}" for value in data[offset:offset + 16]) + ",")
    return f"const uint8_t {name}[] = {{\n" + "\n".join(rows) + "\n};\n"


SCREEN_PALETTES = (
    ((0, 0, 0), (88, 30, 24), (240, 64, 32), (255, 248, 224)),
    ((0, 0, 0), (112, 72, 8), (248, 200, 24), (255, 248, 224)),
    ((0, 0, 0), (48, 80, 8), (152, 208, 24), (255, 248, 224)),
    ((0, 0, 0), (16, 48, 112), (40, 128, 248), (255, 248, 224)),
    ((0, 0, 0), (64, 24, 104), (160, 104, 224), (255, 248, 224)),
    ((0, 0, 0), (8, 72, 80), (80, 200, 224), (255, 248, 224)),
    ((0, 0, 0), (64, 64, 64), (160, 160, 160), (255, 248, 224)),
    ((0, 0, 0), (40, 64, 88), (232, 176, 56), (255, 248, 224)),
)

TITLE_PALETTES = (
    ((189, 197, 173), (189, 197, 165), (189, 189, 165), (82, 99, 82)),
    ((197, 206, 173), (156, 173, 140), (132, 148, 115), (82, 90, 74)),
    ((140, 156, 123), (99, 115, 90), (66, 74, 58), (8, 25, 16)),
    ((189, 197, 173), (165, 173, 148), (115, 123, 107), (16, 33, 25)),
    ((206, 214, 181), (165, 173, 148), (132, 148, 115), (8, 25, 16)),
    ((197, 206, 181), (132, 148, 123), (74, 82, 66), (8, 25, 16)),
    ((189, 197, 173), (140, 148, 123), (82, 99, 82), (8, 25, 16)),
)

TITLE_PALETTE = (
    (230, 255, 206),
    (132, 197, 107),
    (49, 107, 82),
    (0, 25, 33),
)

INTRO_PALETTE = (
    (202, 220, 159),
    (139, 172, 15),
    (48, 98, 48),
    (13, 56, 0),
)

GAME_OVER_PALETTE = (
    (202, 220, 159),
    (139, 172, 15),
    (48, 98, 48),
    (13, 56, 0),
)

START_MENU_PALETTE = (
    (213, 231, 160),
    (149, 186, 104),
    (83, 126, 67),
    (22, 61, 29),
)

RESULTS_PALETTE = (
    (209, 228, 154),
    (139, 178, 99),
    (35, 76, 42),
    (11, 39, 23),
)

CREDITS_PALETTE = (
    (13, 56, 0),
    (48, 98, 48),
    (139, 172, 15),
    (202, 220, 159),
)


def reduce_screen_tiles(tiles, tilemap, limit, protected=(), protected_tile_count=40):
    protected = set(protected) | set(range(min(protected_tile_count, len(tiles))))
    if len(protected) > limit:
        raise ValueError(f"protected screen tiles exceed tile budget: {len(protected)} > {limit}")
    while len(tiles) > limit:
        frequencies = [0] * len(tiles)
        for tile_index in tilemap:
            frequencies[tile_index] += 1
        best = None
        for source_index in range(40, len(tiles)):
            if source_index in protected:
                continue
            source_pixels = tuple(tiles[source_index].getdata())
            for target_index, target_tile in enumerate(tiles):
                if source_index == target_index:
                    continue
                distance = sum(
                    abs(source - target)
                    for source, target in zip(source_pixels, target_tile.getdata())
                )
                candidate = (frequencies[source_index] * distance, distance, source_index, target_index)
                if best is None or candidate < best:
                    best = candidate
        _, _, source_index, target_index = best
        replacement = target_index - (target_index > source_index)
        tilemap = [
            replacement if tile_index == source_index
            else tile_index - (tile_index > source_index)
            for tile_index in tilemap
        ]
        del tiles[source_index]
        protected = {index - (index > source_index) for index in protected}
    return tiles, tilemap


def screen_art(path, size, palettes, crop=None, content_size=None, stretch=False, pixel_scale=1, white_background=False, best_palette=False, screen_boundary=False, tile_limit=255, include_font=True, protected_regions=(), reserved_tiles=(), protected_tile_count=40, font_tiles=None):
    if isinstance(path, Image.Image):
        source = path.convert("RGB")
    else:
        with Image.open(path) as source_file:
            source = source_file.convert("RGB")
    if crop:
        source = source.crop(crop)
    if stretch:
        source = source.resize(content_size or size, Image.Resampling.LANCZOS)
    else:
        source.thumbnail(content_size or size, Image.Resampling.LANCZOS)
    if pixel_scale > 1:
        source = source.resize(
            (source.width // pixel_scale, source.height // pixel_scale),
            Image.Resampling.LANCZOS,
        ).resize(source.size, Image.Resampling.NEAREST)
    if white_background:
        pixels = source.load()
        for y in range(source.height):
            for x in range(source.width):
                if sum(pixels[x, y]) >= 525:
                    pixels[x, y] = (255, 255, 255)
    canvas = Image.new("RGB", size)
    canvas.paste(source, ((size[0] - source.width) // 2, (size[1] - source.height) // 2))
    if screen_boundary:
        background = canvas.getpixel((1, 1))
        boundary_color = max((palettes[0][0], palettes[0][3]), key=lambda color: sum((color[channel] - background[channel]) ** 2 for channel in range(3)))
        ImageDraw.Draw(canvas).rectangle((0, 0, size[0] - 1, size[1] - 1), outline=boundary_color)
    tiles = list(font_tiles) if font_tiles is not None else make_font_tiles() if include_font else [Image.new("L", (8, 8), 0)]
    tiles.extend(reserved_tiles)
    tile_lookup = {bytes(tile.getdata()): index for index, tile in enumerate(tiles)}
    tilemap = []
    attributes = []
    preview = Image.new("RGB", size)
    for top in range(0, size[1], 8):
        for left in range(0, size[0], 8):
            source_tile = canvas.crop((left, top, left + 8, top + 8))
            source_pixels = tuple(source_tile.getdata())
            if best_palette:
                palette_index = min(
                    range(len(palettes)),
                    key=lambda index: sum(
                        min(sum((pixel[channel] - color[channel]) ** 2 for channel in range(3)) for color in palettes[index])
                        for pixel in source_pixels
                    ),
                )
            else:
                colorful = [pixel for pixel in source_pixels if max(pixel) - min(pixel) > 48]
                palette_index = 6
                if colorful:
                    average = tuple(sum(pixel[channel] for pixel in colorful) / len(colorful) for channel in range(3))
                    hue = colorsys.rgb_to_hsv(*(component / 255 for component in average))[0]
                    palette_index = min(range(6), key=lambda index: min(abs(hue - colorsys.rgb_to_hsv(*(component / 255 for component in palettes[index][2]))[0]), 1 - abs(hue - colorsys.rgb_to_hsv(*(component / 255 for component in palettes[index][2]))[0])))
            palette = palettes[palette_index]
            tile = Image.new("L", (8, 8))
            for offset, pixel in enumerate(source_pixels):
                shade = min(range(4), key=lambda index: sum((pixel[channel] - palette[index][channel]) ** 2 for channel in range(3)))
                tile.putpixel((offset % 8, offset // 8), shade)
                preview.putpixel((left + offset % 8, top + offset // 8), palette[shade])
            key = bytes(tile.getdata())
            if key not in tile_lookup:
                tile_lookup[key] = len(tiles)
                tiles.append(tile)
            tilemap.append(tile_lookup[key])
            attributes.append(palette_index)
    protected = set()
    for left, top, right, bottom in protected_regions:
        for tile_y in range(top // 8, (bottom + 7) // 8):
            for tile_x in range(left // 8, (right + 7) // 8):
                protected.add(tilemap[tile_y * (size[0] // 8) + tile_x])
    tiles, tilemap = reduce_screen_tiles(tiles, tilemap, tile_limit, protected, protected_tile_count)
    for tile_position, tile_index in enumerate(tilemap):
        left = (tile_position % (size[0] // 8)) * 8
        top = (tile_position // (size[0] // 8)) * 8
        palette = palettes[attributes[tile_position]]
        pixels = tiles[tile_index].load()
        for y in range(8):
            for x in range(8):
                preview.putpixel((left + x, top + y), palette[pixels[x, y]])
    return tiles, tilemap, attributes, preview


def make_instruction_screen():
    with Image.open(GAMEBOY / "assets" / "instructions_master.png") as master:
        if master.size != (160, 144):
            raise ValueError(f"expected 160x144 instructions artwork, got {master.size}")
        source = master.convert("RGB")
        indexed = source.quantize(colors=4, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    colors = [tuple(indexed.getpalette()[index * 3:index * 3 + 3]) for index in range(4)]
    order = sorted(range(4), key=lambda index: sum(channel * weight for channel, weight in zip(colors[index], (299, 587, 114))), reverse=True)
    palette = [colors[index] for index in order]
    image = grid_shades(source, palette)
    characters = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.+!"
    glyphs = {}
    for character, tile in zip(characters, make_font_tiles(characters)):
        bounds = tile.getbbox()
        glyphs[character] = tile.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (2, 8), 0)
    draw = ImageDraw.Draw(image)
    draw.rectangle((85, 57, 145, 100), fill=0)
    labels = ("1. PLACE DICE", "2. MATCH 3+", "3. MERGE UP", "4. MAKE CHAINS", "5. REACH SIX!")
    for row, text in enumerate(labels):
        left = 87
        top = 58 + row * 8
        for character in text:
            glyph = glyphs[character]
            if left + glyph.width > 146:
                raise ValueError(f"instructions label exceeds its panel: {text}")
            image.paste(glyph, (left, top))
            left += glyph.width + 1
    draw.rectangle((21, 128, 140, 138), fill=0)
    return image, palette


def make_settings_screens():
    with Image.open(GAMEBOY / "assets" / "settings_master.png") as master:
        source = master.convert("RGB").resize((160, 144), Image.Resampling.LANCZOS)
    indexed = source.quantize(colors=4, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    palette = [tuple(indexed.getpalette()[index * 3:index * 3 + 3]) for index in range(4)]
    palette.sort(key=lambda color: sum(channel * weight for channel, weight in zip(color, (299, 587, 114))), reverse=True)
    base = grid_shades(source, palette)
    draw = ImageDraw.Draw(base)
    draw.rectangle((80, 62, 147, 111), fill=base.getpixel((130, 104)))
    draw.rectangle((20, 131, 142, 142), fill=0)
    characters = " SOUNDFLAH"
    glyphs = {}
    for character, tile in zip(characters, make_font_tiles(characters)):
        bounds = tile.getbbox()
        glyphs[character] = tile.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (2, 8), 0)
    screens = []
    for state in range(8):
        image = base.copy()
        draw = ImageDraw.Draw(image)
        for row, label in enumerate(("SOUND", "FLASH")):
            top = 64 + row * 16
            if state // 4 == row:
                draw.rectangle((80, top, 143, top + 11), fill=0)
                draw.polygon(((82, top + 3), (85, top + 6), (82, top + 9)), fill=3)
            value = "ON" if state & (2 if row == 0 else 1) else "OFF"
            for text, left in ((label, 89), (value, 125)):
                for character in text:
                    glyph = glyphs[character]
                    image.paste(3, (left, top + 2, left + glyph.width, top + 10), glyph.point(lambda shade: 255 if shade else 0))
                    left += glyph.width + 1
        screens.append(image)
    return screens, palette


def make_pause_screens():
    with Image.open(GAMEBOY / "assets" / "pause_master.png") as master:
        source = master.convert("RGB").resize((160, 144), Image.Resampling.LANCZOS)
    indexed = source.quantize(colors=4, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    palette = [tuple(indexed.getpalette()[index * 3:index * 3 + 3]) for index in range(4)]
    palette.sort(key=lambda color: sum(channel * weight for channel, weight in zip(color, (299, 587, 114))), reverse=True)
    clean = source.copy()
    text_regions = [(8, top, 101, bottom) for top, bottom in ((41, 52), (55, 66), (69, 80), (83, 96), (97, 111))]
    text_regions.append((9, 130, 145, 139))
    for left, top, right, bottom in text_regions:
        span = bottom - top + 1
        for column in range(left, right):
            upper = source.getpixel((column, top - 1))
            lower = source.getpixel((column, bottom))
            for row in range(top, bottom):
                progress = row - top + 1
                color = tuple((above * (span - progress) + below * progress + span // 2) // span for above, below in zip(upper, lower))
                clean.putpixel((column, row), color)
    base = grid_shades(clean, palette)
    glyphs = {}
    for character, tile in zip(FONT_GLYPH_ORDER, make_font_tiles()):
        bounds = tile.getbbox()
        glyphs[character] = tile.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (2, 8), 0)

    def label(image, text, left, top):
        for character in text:
            glyph = glyphs[character]
            image.paste(3, (left, top, left + glyph.width, top + 8), glyph.point(lambda shade: 255 if shade else 0))
            left += glyph.width + 1

    footer = "A CHOOSE   B RESUME"
    footer_width = sum(glyphs[character].width + 1 for character in footer) - 1
    label(base, footer, (160 - footer_width) // 2, 130)
    screens = []
    for state in range(20):
        image = base.copy()
        labels = ("RESUME", "INSTRUCTIONS", "SOUND ON" if state & 2 else "SOUND OFF", "FLASH FULL" if state & 1 else "FLASH REDUCED", "NEW GAME")
        for row, text in enumerate(labels):
            label(image, text, 24, 42 + row * 14)
        label(image, "+", 10, 42 + (state // 4) * 14)
        screens.append(image)
    return screens, palette


def main():
    font_tiles = make_font_tiles()
    lanky = lanky_glyphs()
    title_prompt = make_title_prompt()
    intro_version_tiles = make_font_tiles("V.0123456789")
    game_mascot = make_game_mascot(GAMEBOY / "assets" / "game_mascot_happy.png")
    score_popup_digits = make_morbidosa_tiles("0123456789")
    merge_particle = make_star()
    merge_particle_tiles = (merge_particle, Image.new("L", (8, 8), 0))
    title_prompt_tiles = [tile for tile in split_tiles(title_prompt) if tile.getbbox()]
    preview_dir = GAMEBOY / "build" / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    prompt_preview = Image.new("RGBA", title_prompt.size, (0, 0, 0, 0))
    prompt_preview.putdata([(*TITLE_PALETTE[3], 255) if value else (0, 0, 0, 0) for value in title_prompt.getdata()])
    prompt_preview.save(preview_dir / "title-prompt.png")
    font_preview = Image.new("L", (64, 40), 0)
    for index, tile in enumerate(font_tiles):
        font_preview.paste(tile.point(lambda value: value * 85), ((index & 7) * 8, (index >> 3) * 8))
    font_preview.resize((512, 320), Image.Resampling.NEAREST).save(preview_dir / "font.png")
    gameplay = [ImageChops.offset(tile, -1, 0) for tile in make_font_tiles(" 0123456789+")]
    score_label = Image.new("L", (24, 8), 0)
    for index, tile in enumerate(make_font_tiles("SCORE")):
        score_label.paste(tile.crop((1, 0, 4, 8)), (index * 5, 0))
    gameplay.extend(split_tiles(score_label))
    next_dice_base = len(gameplay)
    background_pattern = Image.new("L", (8, 8), 0)
    for position in ((1, 1), (5, 5)):
        background_pattern.putpixel(position, 1)

    with Image.open(GAMEBOY / "assets" / "dice" / "tiled_master.png") as master:
        if master.size != (96, 48):
            raise ValueError(f"expected 96x48 dice sheet, got {master.size}")
        dice_sheet = master.convert("RGBA")
    dice = []
    native_sources = {}
    native_dice = {}
    for face, filename in ((0, "one_18x18.png"), (1, "two_18x18.png"), (2, "three_18x18.png"), (3, "four_18x18.png"), (4, "five_18x18.png"), (5, "six_18x18.png")):
        with Image.open(GAMEBOY / "assets" / "dice" / filename) as master:
            if master.size != (18, 18):
                raise ValueError(f"expected native 18x18 die: {filename}, got {master.size}")
            native_sources[face] = master.convert("RGBA")
        native_dice[face] = make_die(native_sources[face])
    save_shading_previews(native_dice, native_sources, preview_dir)
    native_dice = {face: shade_die(die, native_sources[face], FACE_SHADES[face]) for face, die in native_dice.items()}
    for row in range(3):
        variant_dice = []
        for face in range(6):
            die = Image.new("L", (18, 18), 0)
            die.paste(make_die(dice_sheet.crop((face * 16, row * 16, face * 16 + 16, row * 16 + 16))), (1, 1))
            if face in native_dice:
                die = native_dice[face].copy()
                if row == 1:
                    die.putdata([3 - shade if color[3] >= 128 else 0 for shade, color in zip(native_dice[face].getdata(), native_sources[face].getdata())])
                elif row == 2:
                    draw = ImageDraw.Draw(die)
                    draw.line((4, 4, 13, 13), fill=3)
                    draw.line((13, 4, 4, 13), fill=3)
            variant_dice.append(die)
        dice.append(variant_dice)
    dice_preview = Image.new("RGB", (108, 54), GRID_DISPLAY_PALETTE[0])
    for variant, variant_dice in enumerate(dice):
        for face, die in enumerate(variant_dice):
            preview = Image.new("RGB", die.size)
            for y in range(die.height):
                for x in range(die.width):
                    preview.putpixel((x, y), GRID_DISPLAY_PALETTE[die.getpixel((x, y))])
            dice_preview.paste(preview, (face * 18, variant * 18))
    dice_preview.save(preview_dir / "dice.png")

    gameplay.extend(Image.new("L", (8, 8), 0) for _ in range(32))

    cell_rows = []
    cells = []
    cell_preview = Image.new("L", (140, 80), 0)
    cell_states = [(0, 0), (0, 1)]
    cell_states.extend((face, variant) for variant in range(3) for face in range(1, 7))
    cell_states.append((0, 3))
    for state, (face, variant) in enumerate(cell_states):
        cell = make_cell(variant == 1)
        if face:
            cell.paste(dice[variant][face - 1], (1, 1))
        elif variant == 3:
            hatch = Image.new("L", (16, 16), 0)
            for row in range(1, 15):
                for column in range(1, 15):
                    if (column + row) % 6 < 2:
                        hatch.putpixel((column, row), 3)
            cell.paste(hatch, (2, 2))
        cells.append(cell)
        preview_x = face * 20
        preview_y = variant * 20
        cell_preview.paste(cell.point(lambda value: value * 85), (preview_x, preview_y))
        for shift in (0, 4):
            for row in range(20):
                planes = [0, 0]
                for column in range(20):
                    shade = cell.getpixel((column, row))
                    for plane in range(2):
                        planes[plane] |= ((shade >> plane) & 1) << (23 - shift - column)
                for byte_shift in (16, 8, 0):
                    cell_rows.extend((plane >> byte_shift) & 255 for plane in planes)

    next_panel = make_next_panel()
    next_frame = next_panel.crop((0, 8, 48, 56))
    score_frame = Image.new("L", (48, 32), 0)
    score_frame.paste(next_frame.crop((0, 0, 48, 8)), (0, 0))
    for row in range(8, 24):
        score_frame.paste(next_frame.crop((0, 20, 48, 21)), (0, row))
    score_frame.paste(next_frame.crop((0, 40, 48, 48)), (0, 24))
    for index, tile in enumerate(make_font_tiles("SCORE")):
        score_frame.paste(tile.crop((1, 2, 4, 7)), (12 + index * 5, 8))
    score_digits = [tile.crop((1, 2, 4, 7)) for tile in make_font_tiles("0123456789")]
    score_digit_rows = [sum(bool(tile.getpixel((column, row))) << (2 - column) for column in range(3)) for tile in score_digits for row in range(5)]
    next_states = [(first, None, ((15, 15),)) for first in dice[0]]
    next_states.extend(
        (first, second, positions)
        for first in dice[0] for second in dice[0]
        for positions in (((6, 15), (24, 15)), ((15, 6), (15, 24)), ((24, 15), (6, 15)), ((15, 24), (15, 6)))
    )
    next_maps = []
    for first, second, positions in next_states:
        panel = next_frame.copy()
        panel.paste(first, positions[0])
        if second:
            panel.paste(second, positions[1])
        unique = {bytes(64): 0}
        for tile in split_tiles(panel):
            key = bytes(tile.getdata())
            if key not in unique:
                unique[key] = next_dice_base + len(unique) - 1
            next_maps.append(unique[key])
        if len(unique) - 1 > 32:
            raise ValueError(f"Next window exceeds its 32-tile pool: {len(unique) - 1}")

    boundary_base = len(gameplay)
    with Image.open(GAMEBOY / "assets" / "invalid_placement_master.png") as master:
        invalid_source = master.convert("RGB")
    if invalid_source.size != (55, 52):
        raise ValueError(f"expected 55x52 invalid-placement art, got {invalid_source.size}")
    invalid_source.thumbnail((48, 48), Image.Resampling.LANCZOS)
    invalid_overlay = grid_shades(invalid_source)
    invalid_panel = next_panel.crop((0, 8, 48, 56))
    invalid_panel.paste(
        invalid_overlay, ((48 - invalid_overlay.width) // 2, (48 - invalid_overlay.height) // 2),
        invalid_overlay.point(lambda shade: 255 if shade else 0),
    )
    invalid_lookup = {bytes(64): 0}
    invalid_tiles = []
    invalid_map = []
    for tile in split_tiles(invalid_panel):
        key = bytes(tile.getdata())
        if key not in invalid_lookup:
            invalid_lookup[key] = next_dice_base + len(invalid_tiles)
            invalid_tiles.append(tile)
        invalid_map.append(invalid_lookup[key])
    if len(invalid_tiles) > 32:
        raise ValueError(f"invalid-placement overlay exceeds preview tile space: {len(invalid_tiles)}")
    invalid_preview = Image.new("RGB", invalid_panel.size)
    invalid_preview.putdata([GRID_DISPLAY_PALETTE[shade] for shade in invalid_panel.getdata()])
    invalid_preview.save(preview_dir / "invalid-next.png")
    for horizontal, vertical in ((2, None), (1, None), (None, 3), (None, 2), (2, 3), (2, 2), (1, 3), (1, 2)):
        boundary = Image.new("L", (8, 8), 0)
        draw = ImageDraw.Draw(boundary)
        if horizontal is not None:
            draw.line((0, horizontal, 7, horizontal), fill=3)
        if vertical is not None:
            draw.line((vertical, 0, vertical, 7), fill=3)
        gameplay.append(boundary)

    cell_preview.resize((840, 480), Image.Resampling.NEAREST).save(preview_dir / "grid-cells.png")
    next_panel.point(lambda value: value * 85).resize((384, 448), Image.Resampling.NEAREST).save(preview_dir / "next-panel.png")
    layout = Image.new("L", (160, 144), 0)
    for pixel_y in range(6, 142):
        for pixel_x in range(5, 157):
            layout.putpixel((pixel_x, pixel_y), background_pattern.getpixel(((pixel_x - 5) % 8, (pixel_y - 22) % 8)))
    layout_draw = ImageDraw.Draw(layout)
    layout_draw.rectangle((5, 22, 108, 125), fill=0)
    layout_draw.rectangle((109, 14, 156, 53), fill=0)
    layout.paste(score_frame, (109, 14))
    for index in range(5):
        layout.paste(score_digits[0], (121 + index * 5, 32))
    for row in range(5):
        for column in range(5):
            layout.paste(cells[0], (5 + column * 20, 22 + row * 20))
    for position in ((5, 22), (104, 22), (5, 121), (104, 121)):
        layout.putpixel(position, 0)
    layout.paste(next_panel, (109, 70))
    ImageDraw.Draw(layout).rectangle((0, 0, 159, 143), outline=3)
    layout_preview = Image.new("RGB", layout.size)
    layout_preview.putdata([GRID_DISPLAY_PALETTE[shade] for shade in layout.getdata()])
    for pixel_y in range(6, 142):
        for pixel_x in range(5, 157):
            protected = (pixel_x < 109 and 22 <= pixel_y < 126) or (pixel_x >= 109 and (14 <= pixel_y < 54 or 70 <= pixel_y < 126))
            if not protected and layout.getpixel((pixel_x, pixel_y)) == 1:
                layout_preview.putpixel((pixel_x, pixel_y), (190, 210, 148))
    ImageDraw.Draw(layout_preview).rectangle((0, 0, 159, 143), outline=(0, 0, 0))
    layout_preview.save(preview_dir / "gameplay-layout.png")

    if len(gameplay) > 55:
        raise ValueError(f"gameplay tiles overlap the board canvas: {len(gameplay)}")

    title = list(font_tiles)
    title.extend(split_tiles(image_mask(ATARI / "assets" / "game_logo_master.png", (144, 40), 108)))
    title.extend(split_tiles(image_mask(ATARI / "assets" / "high_score_mascot_master.png", (48, 64), 96)))
    if len(title) != 178:
        raise ValueError(f"expected 178 title tiles, got {len(title)}")

    header = f"""#ifndef SIXIES_GENERATED_ART_H
#define SIXIES_GENERATED_ART_H

#include <stdint.h>

#define ART_FONT_COUNT 40u
#define ART_HUD_DIGIT_BASE 1u
#define ART_HUD_PLUS_TILE 11u
#define ART_HUD_SCORE_BASE 12u
#define ART_NEXT_DICE_BASE {next_dice_base}u
#define ART_NEXT_TILES 32u
#define ART_DICE_PIXELS 18u
#define ART_CELL_STATE_COUNT 21u
#define ART_OCCUPIED_CELL_STATE 20u
#define ART_CELL_PIXELS 20u
#define ART_BOARD_BASE 55u
#define ART_BOARD_TILES 169u
#define ART_BOARD_TILE_WIDTH 13u
#define ART_SCREEN_BOUNDARY_BASE {boundary_base}u
#define ART_NEXT_PANEL_WIDTH 6u
#define ART_NEXT_PANEL_HEIGHT 7u
#define ART_INVALID_NEXT_TILES {len(invalid_tiles)}u
#define ART_SCORE_PANEL_BASE 224u
#define ART_SCORE_PANEL_TILES 24u
#define ART_SCORE_PANEL_TOP 31u
#define ART_CALLOUT_TILES 32u
#define ART_CALLOUT_BASE 0u
#define ART_CALLOUT_SPRITES 16u
#define ART_CALLOUT_SPRITE_WIDTH 8u
#define ART_CALLOUT_SPRITE_HEIGHT 2u
#define ART_BACKGROUND_PATTERN_TILE 255u
#define ART_CHAIN_REACTION_BASE 0u
#define ART_CHAIN_REACTION_TILES 32u
#define ART_CHAIN_REACTION_SPRITES 16u
#define ART_CHAIN_REACTION_SPRITE_WIDTH 8u
#define ART_CHAIN_REACTION_SPRITE_HEIGHT 2u
#define ART_CHAIN_REACTION_MAX_SPRITES 16u
#define ART_STAR_TILE 36u
#define ART_MERGE_PARTICLE_TILES 2u
#define ART_SCORE_POPUP_BASE 32u
#define ART_CHAIN_STAR_LOAD_BASE 38u
#define ART_CHAIN_STAR_BASE 38u
#define ART_CHAIN_STAR_TILES 4u
#define ART_GAME_MASCOT_BASE 42u
#define ART_GAME_MASCOT_WIDTH 5u
#define ART_GAME_MASCOT_HEIGHT 6u
#define ART_GAME_MASCOT_TILES 30u
#define ART_GAMEPLAY_TILE_COUNT {len(gameplay)}u

#define ART_TITLE_LOGO_BASE 40u
#define ART_TITLE_MASCOT_BASE 130u
#define ART_TITLE_TILE_COUNT 178u
#define ART_TITLE_PROMPT_WIDTH {title_prompt.width}u
#define ART_TITLE_PROMPT_TILES {len(title_prompt_tiles)}u
#define ART_INTRO_VERSION_BASE 0u
#define ART_INTRO_VERSION_TILES {len(intro_version_tiles)}u
#define ART_INTRO_VERSION_V_TILE ART_INTRO_VERSION_BASE
#define ART_INTRO_VERSION_DOT_TILE (ART_INTRO_VERSION_BASE + 1u)
#define ART_INTRO_VERSION_DIGIT_BASE (ART_INTRO_VERSION_BASE + 2u)

extern const uint8_t gameplay_tiles[];
extern const uint8_t gameplay_cell_rows[];
extern const uint8_t gameplay_next_frame[];
extern const uint8_t gameplay_next_dice_rows[];
extern const uint8_t gameplay_next_maps[];
extern const uint8_t title_tiles[];

#endif
"""
    header = header.replace("#include <stdint.h>", "#include <gb/gb.h>\n#include <stdint.h>")
    header = header.replace("#endif", "#define ART_BORDER_BASE 178u\n#define ART_SCORE_MASCOT_BASE 184u\nvoid art_load_game(void) BANKED;\nvoid art_draw_cell(uint8_t x, uint8_t y, uint8_t state, uint8_t board_index) BANKED;\nvoid art_draw_next_panel(uint8_t x, uint8_t y) BANKED;\nvoid art_load_title(void) BANKED;\nvoid art_load_credits(void) BANKED;\nvoid art_load_callout(uint8_t index) BANKED;\nvoid art_load_chain_reaction(void) BANKED;\nvoid art_load_screen(uint8_t index) BANKED;\nvoid art_load_credits_screen(void) BANKED;\n\n#endif")
    floor = make_floor()
    mascot_frames = make_mascot()
    header = header.replace("void art_load_game(void) BANKED;", "void art_load_game(void) BANKED;\nvoid art_reset_board(void) BANKED;\nvoid art_restore_next_dice(void) BANKED;\nvoid art_draw_invalid_next(uint8_t x, uint8_t y) BANKED;\nvoid art_load_menu_font(void) BANKED;")
    header = header.replace("void art_reset_board(void) BANKED;", "void art_reset_board(void) BANKED;\nvoid art_shift_board(uint8_t shifted) BANKED;")
    header = header.replace("#endif", "uint8_t art_build_score_popup(uint16_t value) BANKED;\n\n#endif")
    header = header.replace("void art_load_callout(uint8_t index) BANKED;", "void art_draw_callout(uint8_t index) BANKED;\nvoid art_clear_callout(void) BANKED;\nvoid art_draw_score(uint16_t value) BANKED;")
    header = header.replace("void art_draw_next_panel(uint8_t x, uint8_t y) BANKED;", "void art_draw_next_dice(uint8_t x, uint8_t y, uint8_t first, uint8_t second, uint8_t orientation) BANKED;")
    header = header.replace("void art_restore_next_dice(void) BANKED;\n", "")
    header = header.replace("void art_draw_callout(uint8_t index) BANKED;", "void art_draw_callout(uint8_t index, uint8_t x, uint8_t y) BANKED;")
    header = header.replace("void art_load_menu_font(void) BANKED;", "void art_load_menu_font(void) BANKED;\nvoid art_load_merge_particle(void) BANKED;\nvoid art_restore_game_sprite_font(void) BANKED;")
    board_source = '#pragma bank 7\n#include <stdint.h>\n\n' + c_array("gameplay_cell_rows", cell_rows)
    board_source += c_array("gameplay_next_frame", pack_tiles(split_tiles(next_frame)))
    next_dice_rows = []
    for die in dice[0]:
        for shift in (0, 6, 7):
            for row in range(18):
                planes = [0, 0]
                for column in range(18):
                    shade = die.getpixel((column, row))
                    for plane in range(2):
                        planes[plane] |= ((shade >> plane) & 1) << (31 - shift - column)
                for byte_shift in (24, 16, 8, 0):
                    next_dice_rows.extend((plane >> byte_shift) & 255 for plane in planes)
    board_source += c_array("gameplay_next_dice_rows", next_dice_rows)
    board_source += c_array("gameplay_next_maps", next_maps)
    (GAMEBOY / "src" / "generated_board.c").write_text(board_source)
    source = "#pragma bank 1\n#include <gb/gb.h>\n#include \"generated_art.h\"\n\n" + c_array("gameplay_tiles", pack_tiles(gameplay)) + "\n" + c_array("title_tiles", pack_tiles(title))
    source += c_array("gameplay_sprite_font_tiles", pack_tiles(font_tiles))
    source += c_array("gameplay_background_pattern", pack_tiles([background_pattern]))
    source += c_array("gameplay_score_frame", pack_tiles(split_tiles(score_frame)))
    source += c_array("gameplay_score_digits", score_digit_rows)
    source += c_array("gameplay_score_map", list(range(224, 248)))
    source = source.replace('#include <gb/gb.h>', '#include <gb/gb.h>\n#include <string.h>', 1)
    menu_font_tiles = []
    for character in FONT_GLYPH_ORDER:
        tile = Image.new("L", (8, 8), 0)
        tile.paste(lanky[character], (0, 0))
        menu_font_tiles.append(tile)
    source += c_array("menu_font_tiles", pack_tiles(menu_font_tiles))
    source += "\nvoid art_load_menu_font(void) BANKED { set_bkg_data(0u, 40u, menu_font_tiles); }\n"
    game_logo = game_logo_wordmark((80, 24))
    source += c_array("credits_logo_tiles", pack_tiles(split_tiles(logo_wordmark((96, 24)))))
    source += c_array("score_mascot_tiles", pack_tiles(split_tiles(image_mask(ATARI / "assets" / "high_score_mascot_master.png", (32, 32), 96))))
    borders = []
    for horizontal, vertical in ((True, False), (False, True), (True, True)):
        border = Image.new("L", (8, 8), 0)
        draw = ImageDraw.Draw(border)
        if horizontal:
            draw.line((0, 2, 7, 2), fill=2)
            draw.line((0, 5, 7, 5), fill=2)
        if vertical:
            draw.line((2, 0, 2, 7), fill=2)
            draw.line((5, 0, 5, 7), fill=2)
        borders.append(border)
    source += c_array("border_tiles", pack_tiles(borders))
    source += c_array("score_popup_digits", pack_tiles(score_popup_digits))
    source += c_array("merge_particle_tiles", pack_tiles(merge_particle_tiles))
    mascot_tiles = split_tiles(game_mascot)
    source += c_array("game_mascot_tiles", pack_tiles(mascot_tiles))
    source += """
void art_load_merge_particle(void) BANKED {
    set_sprite_data(ART_STAR_TILE, ART_MERGE_PARTICLE_TILES, merge_particle_tiles);
}

void art_restore_game_sprite_font(void) BANKED {
    set_sprite_data(0u, ART_FONT_COUNT, gameplay_sprite_font_tiles);
}

void art_load_game(void) BANKED {
    LCDC_REG &= (uint8_t)~LCDCF_BG8000;
    set_bkg_data(0u, ART_GAMEPLAY_TILE_COUNT, gameplay_tiles);
    set_bkg_data(ART_BACKGROUND_PATTERN_TILE, 1u, gameplay_background_pattern);
    art_restore_game_sprite_font();
    set_sprite_data(ART_GAME_MASCOT_BASE, ART_GAME_MASCOT_TILES, game_mascot_tiles);
    art_reset_board();
}

uint8_t art_build_score_popup(uint16_t value) BANKED {
    uint8_t pixels[48] = {0};
    uint16_t remaining = value;
    uint8_t count = 1u;
    uint8_t position;
    uint8_t digit;

    while (remaining >= 10u) { remaining /= 10u; ++count; }
    if (count > 3u) count = 3u;
    for (position = count; position; --position) {
        digit = value % 10u;
        value /= 10u;
        memcpy(pixels + (position - 1u) * 16u, score_popup_digits + digit * 16u, 16u);
    }
    set_sprite_data(ART_SCORE_POPUP_BASE, 3u, pixels);
    return count * 8u;
}

void art_draw_score(uint16_t value) BANKED {
    uint8_t pixels[ART_SCORE_PANEL_TILES * 16u];
    uint8_t position;
    uint8_t row;
    uint8_t column;
    uint8_t digit;
    uint8_t pixel_x;
    uint8_t pixel_y;
    uint8_t mask;
    uint16_t offset;

    memcpy(pixels, gameplay_score_frame, sizeof(pixels));
    for (position = 5u; position; --position) {
        digit = value % 10u;
        value /= 10u;
        for (row = 0u; row < 5u; ++row) {
            pixel_y = 18u + row;
            for (column = 0u; column < 3u; ++column) {
                if (!(gameplay_score_digits[digit * 5u + row] & (4u >> column))) continue;
                pixel_x = 12u + (position - 1u) * 5u + column;
                offset = ((uint16_t)(pixel_y >> 3) * 6u + (pixel_x >> 3)) * 16u + (pixel_y & 7u) * 2u;
                mask = 0x80u >> (pixel_x & 7u);
                pixels[offset] |= mask;
                pixels[offset + 1u] |= mask;
            }
        }
    }
    set_bkg_data(ART_SCORE_PANEL_BASE, ART_SCORE_PANEL_TILES, pixels);
    for (row = 0u; row < 4u; ++row) {
        set_bkg_tiles(13u, (ART_SCORE_PANEL_TOP + row) & 31u, 6u, 1u, gameplay_score_map + row * 6u);
    }
}

void art_load_title(void) BANKED {
    set_bkg_data(0u, ART_TITLE_TILE_COUNT, title_tiles);
    set_bkg_data(ART_BORDER_BASE, 3u, border_tiles);
    set_bkg_data(ART_SCORE_MASCOT_BASE, 16u, score_mascot_tiles);
}

void art_load_credits(void) BANKED {
    set_bkg_data(ART_TITLE_LOGO_BASE, 36u, credits_logo_tiles);
}

"""
    game_logo_preview = Image.new("RGB", game_logo.size)
    for y in range(game_logo.height):
        for x in range(game_logo.width):
            game_logo_preview.putpixel((x, y), GRID_PALETTE[game_logo.getpixel((x, y))])
    game_logo_preview.save(preview_dir / "game-logo.png")
    floor_preview = Image.new("RGB", floor.size)
    for y in range(floor.height):
        for x in range(floor.width):
            floor_preview.putpixel((x, y), GRID_PALETTE[floor.getpixel((x, y))])
    floor_preview.save(preview_dir / "floor.png")
    mascot_preview = Image.new("RGB", (48 * len(mascot_frames), 64), GRID_PALETTE[0])
    for frame_index, frame in enumerate(mascot_frames):
        for y in range(frame.height):
            for x in range(frame.width):
                mascot_preview.putpixel((frame_index * 48 + x, y), GRID_PALETTE[frame.getpixel((x, y))])
    mascot_preview.save(preview_dir / "mascot-walk.png")
    instruction_image, instruction_colors = make_instruction_screen()
    instruction_pages = [instruction_image]
    instruction_tiles = []
    instruction_lookup = {bytes(tile.getdata()): index for index, tile in enumerate(instruction_tiles)}
    instruction_maps = []
    instruction_sheet = Image.new("RGB", (160, 144), instruction_colors[0])
    for page, instruction_image in enumerate(instruction_pages):
        for tile in split_tiles(instruction_image):
            key = bytes(tile.getdata())
            if key not in instruction_lookup:
                instruction_lookup[key] = len(instruction_tiles)
                instruction_tiles.append(tile)
            instruction_maps.append(instruction_lookup[key])
        preview = Image.new("RGB", instruction_image.size)
        preview.putdata([instruction_colors[shade] for shade in instruction_image.getdata()])
        preview.save(preview_dir / f"instructions-{page + 1}.png")
        instruction_sheet.paste(preview, ((page % 3) * 160, (page // 3) * 144))
    if len(instruction_tiles) > 256:
        raise ValueError(f"instruction images exceed background tile space: {len(instruction_tiles)}")
    instruction_sheet.save(preview_dir / "instructions-sheet.png")
    instruction_palette = bytearray()
    for red, green, blue in instruction_colors:
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        instruction_palette.extend((color & 255, color >> 8))
    instruction_source = '#pragma bank 1\n#include <gb/gb.h>\n#include <gb/cgb.h>\n#include "generated_art.h"\n\n'
    instruction_source += c_array("instruction_tiles", pack_tiles(instruction_tiles))
    instruction_source += c_array("instruction_maps", instruction_maps)
    instruction_source += c_array("instruction_palette", instruction_palette)
    instruction_source += f"""
void art_load_instructions(void) BANKED {{
    LCDC_REG &= (uint8_t)~LCDCF_BG8000;
    set_bkg_data(0u, {len(instruction_tiles)}u, instruction_tiles);
    if (_cpu == CGB_TYPE) set_bkg_palette(0u, 1u, (const palette_color_t *)instruction_palette);
}}

void art_draw_instructions(uint8_t page) BANKED {{
    set_bkg_tiles(0u, 0u, 20u, 18u, instruction_maps + (uint16_t)page * 360u);
}}
"""
    (GAMEBOY / "src" / "generated_instructions.c").write_text(instruction_source)
    header = header.replace("#endif", f"""#define ART_INSTRUCTION_PAGES {len(instruction_pages)}u
void art_load_instructions(void) BANKED;
void art_draw_instructions(uint8_t page) BANKED;

#endif""")
    with Image.open(GAMEBOY / "assets" / "results_menu_mockup.png") as master:
        results = master.convert("RGB")
    if results.size != (160, 144):
        raise ValueError(f"expected 160x144 results mockup, got {results.size}")
    arrow = grid_shades(results.crop((70, 84, 78, 100)), RESULTS_PALETTE)
    results = grid_shades(results, RESULTS_PALETTE)
    draw = ImageDraw.Draw(results)
    draw.rectangle((62, 29, 143, 73), fill=0)
    draw.rectangle((70, 82, 142, 108), fill=0)
    lanky_text(results, "GAME OVER", 68, 32, lanky)
    lanky_text(results, "Score", 71, 52, lanky)
    lanky_text(results, "Best", 71, 64, lanky)
    lanky_text(results, "Try Again", 82, 85, lanky)
    lanky_text(results, "Main Menu", 82, 99, lanky)
    results_rgb = Image.new("RGB", results.size)
    results_rgb.putdata([RESULTS_PALETTE[shade] for shade in results.getdata()])
    result_tiles, result_map, result_attributes, result_preview = screen_art(
        results_rgb, (160, 144), (RESULTS_PALETTE,), best_palette=True,
        screen_boundary=True, tile_limit=240,
        protected_regions=((64, 24, 144, 112),),
    )
    result_palette = bytearray()
    for red, green, blue in RESULTS_PALETTE:
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        result_palette.extend((color & 255, color >> 8))
    result_source = '#pragma bank 6\n#include <stdint.h>\n\n'
    result_source += c_array("results_tiles", pack_tiles(result_tiles))
    result_source += c_array("results_map", result_map)
    result_source += c_array("results_attributes", result_attributes)
    result_source += c_array("results_palette", result_palette)
    result_source += c_array("results_arrow_tiles", pack_tiles(split_tiles(arrow)))
    result_source += c_array("results_digit_rows", [sum((1 << (5 - column)) for column in range(glyph.width) if glyph.getpixel((column, row))) for character in "0123456789" for glyph in (lanky[character],) for row in range(8)])
    (GAMEBOY / "src" / "generated_results.c").write_text(result_source)
    result_preview.save(preview_dir / "results.png")
    header = header.replace("#endif", f"""#define ART_RESULTS_TILE_COUNT {len(result_tiles)}u
#define ART_RESULTS_NUMBER_BASE 240u
extern const uint8_t results_tiles[];
extern const uint8_t results_map[];
extern const uint8_t results_attributes[];
extern const uint8_t results_palette[];
extern const uint8_t results_arrow_tiles[];
extern const uint8_t results_digit_rows[];
void art_load_results(uint16_t score, uint16_t best) BANKED;

#endif""")
    highscore_palette = ((214, 240, 168), (143, 187, 106), (78, 125, 64), (24, 61, 30))
    with Image.open(GAMEBOY / "assets" / "highscore_master.png") as master:
        highscore = master.convert("RGB")
    if highscore.size != (160, 144):
        raise ValueError(f"expected 160x144 high-score template, got {highscore.size}")
    draw = ImageDraw.Draw(highscore)
    draw.rectangle((84, 58, 147, 116), fill=highscore_palette[1])
    draw.rectangle((0, 128, 159, 143), fill=highscore_palette[0])
    highscore_tiles, highscore_map, highscore_attributes, highscore_preview = screen_art(
        highscore, (160, 144), (highscore_palette,), best_palette=True,
        tile_limit=164, include_font=False, protected_regions=((0, 0, 160, 48),),
    )
    highscore_colors = bytearray()
    for red, green, blue in highscore_palette:
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        highscore_colors.extend((color & 255, color >> 8))
    highscore_source = '#pragma bank 5\n#include <stdint.h>\n\n'
    highscore_source += c_array("highscore_tiles", pack_tiles(highscore_tiles))
    highscore_source += c_array("highscore_map", highscore_map)
    highscore_source += c_array("highscore_palette", highscore_colors)
    highscore_source += c_array("highscore_panel", pack_tiles(split_tiles(grid_shades(highscore_preview.crop((80, 56, 152, 120)), highscore_palette))))
    highscore_characters = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ /:"
    highscore_glyphs = {}
    for character, tile in zip(highscore_characters, make_font_tiles(highscore_characters)):
        bounds = tile.getbbox()
        highscore_glyphs[character] = tile.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (2, 8), 0)
    highscore_source += c_array("highscore_glyph_widths", [highscore_glyphs[character].width for character in highscore_characters])
    highscore_source += c_array("highscore_glyph_rows", [sum(0x80 >> column for column in range(highscore_glyphs[character].width) if highscore_glyphs[character].getpixel((column, row))) for character in highscore_characters for row in range(8)])
    (GAMEBOY / "src" / "generated_highscores.c").write_text(highscore_source)
    highscore_preview.save(preview_dir / "highscores.png")
    header = header.replace("#endif", f"""#define ART_HIGHSCORE_TILE_COUNT {len(highscore_tiles)}u
#define ART_HIGHSCORE_PANEL_BASE 164u
#define ART_HIGHSCORE_FOOTER_BASE 236u
extern const uint8_t highscore_tiles[];
extern const uint8_t highscore_map[];
extern const uint8_t highscore_palette[];
extern const uint8_t highscore_panel[];
extern const uint8_t highscore_glyph_widths[];
extern const uint8_t highscore_glyph_rows[];
void art_load_highscores(void) BANKED;
void art_update_highscores(uint8_t page, uint8_t rank, uint8_t letter) BANKED;

#endif""")
    with Image.open(GAMEBOY / "assets" / "start_menu_master.png") as master:
        menu_source = master.convert("RGB")
    if menu_source.size != (160, 144):
        raise ValueError(f"expected 160x144 start menu, got {menu_source.size}")
    menu = grid_shades(menu_source, START_MENU_PALETTE)
    menu_arrow = menu.crop((82, 64, 90, 80))
    draw = ImageDraw.Draw(menu)
    draw.rectangle((91, 63, 152, 79), fill=0)
    draw.rectangle((82, 64, 89, 79), fill=0)
    draw.rectangle((96, 64, 150, 118), fill=0)
    for text, top in (("Play", 67), ("Settings", 81), ("How to Play", 94), ("High Scores", 107)):
        lanky_text(menu, text, 96, top, lanky)
    draw.rectangle((16, 128, 144, 136), fill=0)
    lanky_text(menu, "Roll + Place + Chain!", 20, 128, lanky)
    menu_image = Image.new("RGB", menu.size)
    menu_image.putdata([START_MENU_PALETTE[shade] for shade in menu.getdata()])
    menu_tiles, menu_map, menu_attributes, menu_preview = screen_art(
        menu_image, (160, 144), (START_MENU_PALETTE,), best_palette=True, tile_limit=224, include_font=False,
        protected_regions=((96, 64, 152, 120), (16, 128, 144, 136)),
    )
    option_tops = (64, 79, 92, 105)
    selection_tiles = []
    for selection, top in enumerate(option_tops):
        selected_menu = menu.copy()
        ImageDraw.Draw(selected_menu).rounded_rectangle((92, top, 151, top + 14), radius=3, fill=1, outline=3)
        label = menu.crop((96, top + 2, 150, top + 12))
        selected_menu.paste(label, (96, top + 2), label.point(lambda shade: 255 if shade >= 2 else 0))
        tile_top = top // 8 * 8
        selection_tiles.extend(split_tiles(selected_menu.crop((88, tile_top, 152, tile_top + 24))))
        selected_preview = Image.new("RGB", menu.size)
        selected_preview.putdata([START_MENU_PALETTE[shade] for shade in selected_menu.getdata()])
        selected_preview.save(preview_dir / f"start-menu-{selection}.png")
    menu_palette = bytearray()
    for red, green, blue in START_MENU_PALETTE:
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        menu_palette.extend((color & 255, color >> 8))
    menu_source = '#pragma bank 4\n#include <gb/gb.h>\n#include <gb/cgb.h>\n#include "generated_art.h"\n'
    menu_source += c_array("start_menu_tiles", pack_tiles(menu_tiles))
    menu_source += c_array("start_menu_map", menu_map)
    menu_source += c_array("start_menu_attributes", menu_attributes)
    menu_source += c_array("start_menu_palette", menu_palette)
    menu_source += c_array("start_menu_arrow_tiles", pack_tiles(split_tiles(menu_arrow)))
    menu_source += c_array("start_menu_selection_tiles", pack_tiles(selection_tiles))
    menu_source += f"""
void art_load_start_menu(void) BANKED {{
    LCDC_REG &= (uint8_t)~LCDCF_BG8000;
    set_bkg_data(0u, {len(menu_tiles)}u, start_menu_tiles);
    set_bkg_tiles(0u, 0u, 20u, 18u, start_menu_map);
    set_sprite_data(0u, 2u, start_menu_arrow_tiles);
    if (_cpu == CGB_TYPE) {{
        set_bkg_palette(0u, 1u, (const palette_color_t *)start_menu_palette);
        set_sprite_palette(0u, 1u, (const palette_color_t *)start_menu_palette);
        VBK_REG = 1u;
        set_bkg_tiles(0u, 0u, 20u, 18u, start_menu_attributes);
        VBK_REG = 0u;
    }}
}}

void art_select_start_menu(uint8_t selection, uint8_t previous) BANKED {{
    static const uint8_t tile_tops[4] = {{8u, 9u, 11u, 13u}};
    uint8_t tiles[24];
    uint8_t index;

    if (previous < 4u) {{
        for (index = 0u; index < 3u; ++index) {{
            set_bkg_tiles(11u, tile_tops[previous] + index, 8u, 1u,
                start_menu_map + (uint16_t)(tile_tops[previous] + index) * 20u + 11u);
        }}
    }}
    for (index = 0u; index < 24u; ++index) tiles[index] = 224u + index;
    set_bkg_data(224u, 24u, start_menu_selection_tiles + (uint16_t)selection * 384u);
    set_bkg_tiles(11u, tile_tops[selection], 8u, 3u, tiles);
}}
"""
    (GAMEBOY / "src" / "generated_start_menu.c").write_text(menu_source)
    header = header.replace("#endif", "void art_load_start_menu(void) BANKED;\nvoid art_select_start_menu(uint8_t selection, uint8_t previous) BANKED;\n\n#endif")
    settings_screens, settings_colors = make_settings_screens()
    settings_tiles = []
    settings_lookup = {}
    settings_maps = []
    settings_options = []
    for state, settings_image in enumerate(settings_screens):
        tilemap = []
        for tile in split_tiles(settings_image):
            key = bytes(tile.getdata())
            if key not in settings_lookup:
                settings_lookup[key] = len(settings_tiles)
                settings_tiles.append(tile)
            tilemap.append(settings_lookup[key])
        settings_maps.append(tilemap)
        settings_options.extend(tilemap[row * 20 + column] for row in range(8, 12) for column in range(10, 18))
        preview = Image.new("RGB", (160, 144))
        preview.putdata([settings_colors[shade] for shade in settings_image.getdata()])
        preview.save(preview_dir / f"settings-{state}.png")
    if len(settings_tiles) > 256:
        raise ValueError(f"settings images exceed background tile space: {len(settings_tiles)}")
    settings_palette = bytearray()
    for red, green, blue in settings_colors:
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        settings_palette.extend((color & 255, color >> 8))
    settings_source = '#pragma bank 4\n#include <gb/gb.h>\n#include <gb/cgb.h>\n#include "generated_art.h"\n\n'
    settings_source += c_array("settings_tiles", pack_tiles(settings_tiles))
    settings_source += c_array("settings_map", settings_maps[0])
    settings_source += c_array("settings_option_maps", settings_options)
    settings_source += c_array("settings_palette", settings_palette)
    settings_source += f"""
void art_load_settings(void) BANKED {{
    LCDC_REG &= (uint8_t)~LCDCF_BG8000;
    set_bkg_data(0u, {len(settings_tiles)}u, settings_tiles);
    set_bkg_tiles(0u, 0u, 20u, 18u, settings_map);
    if (_cpu == CGB_TYPE) set_bkg_palette(0u, 1u, (const palette_color_t *)settings_palette);
}}

void art_update_settings(uint8_t state) BANKED {{
    set_bkg_tiles(10u, 8u, 8u, 4u, settings_option_maps + (uint16_t)state * 32u);
}}
"""
    (GAMEBOY / "src" / "generated_settings.c").write_text(settings_source)
    header = header.replace("#endif", "void art_load_settings(void) BANKED;\nvoid art_update_settings(uint8_t state) BANKED;\n\n#endif")
    pause_screens, pause_colors = make_pause_screens()
    pause_tiles = []
    pause_lookup = {}
    pause_maps = []
    for state, pause_image in enumerate(pause_screens):
        tilemap = []
        for tile in split_tiles(pause_image):
            key = bytes(tile.getdata())
            if key not in pause_lookup:
                pause_lookup[key] = len(pause_tiles)
                pause_tiles.append(tile)
            tilemap.append(pause_lookup[key])
        pause_maps.append(tilemap)
        preview = Image.new("RGB", (160, 144))
        preview.putdata([pause_colors[shade] for shade in pause_image.getdata()])
        preview.save(preview_dir / f"pause-{state}.png")
    if len(pause_tiles) > 256:
        raise ValueError(f"pause images exceed background tile space: {len(pause_tiles)}")
    pause_palette = bytearray()
    for red, green, blue in pause_colors:
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        pause_palette.extend((color & 255, color >> 8))
    pause_source = '#pragma bank 5\n#include <gb/gb.h>\n#include <gb/cgb.h>\n#include "generated_art.h"\n\n'
    pause_source += c_array("pause_tiles", pack_tiles(pause_tiles))
    pause_source += c_array("pause_map", pause_maps[0])
    pause_source += c_array("pause_cursor_maps", [pause_maps[selection * 4][row * 20 + 1] for selection in range(5) for row in range(5, 14)])
    pause_source += c_array("pause_sound_maps", [pause_maps[enabled * 2][row * 20 + column] for enabled in range(2) for row in range(8, 10) for column in range(3, 12)])
    pause_source += c_array("pause_flash_maps", [pause_maps[enabled][row * 20 + column] for enabled in range(2) for row in range(10, 12) for column in range(3, 12)])
    pause_source += c_array("pause_palette", pause_palette)
    pause_source += f"""
void art_load_pause(void) BANKED {{
    LCDC_REG &= (uint8_t)~LCDCF_BG8000;
    set_bkg_data(0u, {len(pause_tiles)}u, pause_tiles);
    set_bkg_tiles(0u, 0u, 20u, 18u, pause_map);
    if (_cpu == CGB_TYPE) set_bkg_palette(0u, 1u, (const palette_color_t *)pause_palette);
}}

void art_update_pause(uint8_t selection, uint8_t sound, uint8_t full_flash) BANKED {{
    set_bkg_tiles(1u, 5u, 1u, 9u, pause_cursor_maps + (uint16_t)selection * 9u);
    set_bkg_tiles(3u, 8u, 9u, 2u, pause_sound_maps + (uint16_t)sound * 18u);
    set_bkg_tiles(3u, 10u, 9u, 2u, pause_flash_maps + (uint16_t)full_flash * 18u);
}}
"""
    (GAMEBOY / "src" / "generated_pause.c").write_text(pause_source)
    header = header.replace("#endif", "void art_load_pause(void) BANKED;\nvoid art_update_pause(uint8_t selection, uint8_t sound, uint8_t full_flash) BANKED;\n\n#endif")
    (GAMEBOY / "include" / "generated_art.h").write_text(header)
    (GAMEBOY / "src" / "generated_art.c").write_text(source)
    callout_images = [
        make_callout(GAMEBOY / "assets" / "callouts" / "comic" / f"{CALLOUT_TEMPLATES[name]}.png")
        for name in CALLOUTS
    ]
    chain_reaction = make_chain_reaction_sprite(GAMEBOY / "assets" / "chain_reaction.png")
    chain_stars = make_chain_stars(GAMEBOY / "assets" / "chain_stars_master.png")
    callout_source = '#pragma bank 6\n#include <gb/gb.h>\n#include <gb/cgb.h>\n#include "generated_art.h"\n\n'
    callout_tiles = []
    for image in callout_images:
        tiles = split_tiles(image)
        for row in range(CALLOUT_SPRITE_HEIGHT):
            for column in range(CALLOUT_SPRITE_WIDTH):
                callout_tiles.extend((tiles[(row * 2) * CALLOUT_SPRITE_WIDTH + column], tiles[(row * 2 + 1) * CALLOUT_SPRITE_WIDTH + column]))
    callout_source += c_array("callout_tiles", pack_tiles(callout_tiles))
    chain_reaction_source_tiles = split_tiles(chain_reaction)
    chain_reaction_tiles = []
    for row in range(CALLOUT_SPRITE_HEIGHT):
        for column in range(CALLOUT_SPRITE_WIDTH):
            chain_reaction_tiles.extend((
                chain_reaction_source_tiles[(row * 2) * CALLOUT_SPRITE_WIDTH + column],
                chain_reaction_source_tiles[(row * 2 + 1) * CALLOUT_SPRITE_WIDTH + column],
            ))
    callout_source += c_array("chain_reaction_tiles", pack_tiles(chain_reaction_tiles))
    chain_star_tiles = split_tiles(chain_stars[0])
    callout_source += c_array("chain_star_tiles", pack_tiles((chain_star_tiles[0], chain_star_tiles[2], chain_star_tiles[1], chain_star_tiles[3])))
    callout_source += c_array("chain_star_dmg_tiles", pack_tiles((make_dmg_chain_star(chain_stars[0]), Image.new("L", (8, 8), 0))))
    callout_source += c_array("invalid_next_tiles", pack_tiles(invalid_tiles))
    callout_source += c_array("invalid_next_map", invalid_map)
    callout_source += """
void art_draw_callout(uint8_t index, uint8_t x, uint8_t y) BANKED {
    const uint8_t *source = callout_tiles + (uint16_t)index * ART_CALLOUT_TILES * 16u;
    uint8_t row;
    uint8_t column;
    uint8_t sprite = 3u;

    LCDC_REG |= LCDCF_OBJ16;
    set_sprite_data(ART_CALLOUT_BASE, ART_CALLOUT_TILES, source);
    for (row = 0u; row < ART_CALLOUT_SPRITE_HEIGHT; ++row) {
        for (column = 0u; column < ART_CALLOUT_SPRITE_WIDTH; ++column) {
            set_sprite_tile(sprite, ART_CALLOUT_BASE + (row * ART_CALLOUT_SPRITE_WIDTH + column) * 2u);
            set_sprite_prop(sprite, _cpu == CGB_TYPE ? 5u : 0u);
            move_sprite(sprite, x + column * 8u + 8u, y + row * 16u + 16u);
            ++sprite;
        }
    }
    SHOW_SPRITES;
}

void art_clear_callout(void) BANKED {
    uint8_t sprite;

    for (sprite = 3u; sprite < 3u + ART_CALLOUT_SPRITES; ++sprite) {
        move_sprite(sprite, 0u, 0u);
        set_sprite_prop(sprite, 0u);
    }
    LCDC_REG &= (uint8_t)~LCDCF_OBJ16;
    art_restore_game_sprite_font();
}

void art_load_chain_reaction(void) BANKED {
    set_sprite_data(ART_CHAIN_REACTION_BASE, ART_CHAIN_REACTION_TILES, chain_reaction_tiles);
    if (_cpu == CGB_TYPE) {
        set_sprite_data(ART_CHAIN_STAR_LOAD_BASE, ART_CHAIN_STAR_TILES, chain_star_tiles);
    } else {
        set_sprite_data(ART_CHAIN_STAR_LOAD_BASE, 2u, chain_star_dmg_tiles);
    }
}

void art_draw_invalid_next(uint8_t x, uint8_t y) BANKED {
    set_bkg_data(ART_NEXT_DICE_BASE, ART_INVALID_NEXT_TILES, invalid_next_tiles);
    set_bkg_tiles(x, y, 6u, 6u, invalid_next_map);
}

"""
    (GAMEBOY / "src" / "generated_callouts.c").write_text(callout_source)
    callout_preview = Image.new("RGBA", (128, 160))
    for index, callout in enumerate(callout_images):
        preview = Image.new("RGBA", callout.size)
        for y in range(callout.height):
            for x in range(callout.width):
                shade = callout.getpixel((x, y))
                if shade:
                    preview.putpixel((x, y), CALLOUT_DISPLAY_PALETTE[shade])
        callout_preview.alpha_composite(preview, ((index & 1) * 64, (index >> 1) * 32))
    callout_preview.save(preview_dir / "callouts.png")
    chain_reaction_preview = Image.new("RGBA", chain_reaction.size, (0, 0, 0, 0))
    visible_palette = (GRID_PALETTE[0], GRID_PALETTE[0], GRID_PALETTE[2], GRID_PALETTE[3])
    for y in range(chain_reaction.height):
        for x in range(chain_reaction.width):
            color = chain_reaction.getpixel((x, y))
            if color:
                chain_reaction_preview.putpixel((x, y), visible_palette[color] + (255,))
    chain_reaction_preview.save(preview_dir / "chain-reaction.png")
    star_preview = Image.new("RGBA", (16, 8))
    for variant, star in enumerate(chain_stars):
        for row in range(8):
            for column in range(8):
                shade = star.getpixel((column, row))
                if shade:
                    star_preview.putpixel((variant * 8 + column, row), CHAIN_STAR_PALETTES[variant][shade] + (255,))
    star_preview.resize((256, 128), Image.Resampling.NEAREST).save(preview_dir / "chain-stars.png")
    screen_source = '#pragma bank 2\n#include <gb/gb.h>\n#include <gb/cgb.h>\n#include "generated_art.h"\n'
    screen_source += c_array("title_prompt_tiles", pack_tiles(title_prompt_tiles))
    screen_source += c_array("intro_version_tiles", pack_tiles(intro_version_tiles))
    loaders = []
    for index, (name, path, size, palettes, crop, content_size, stretch, pixel_scale, white_background, best_palette) in enumerate((
        ("title", GAMEBOY / "assets" / "title_master.png", (160, 144), (TITLE_PALETTE,), None, None, False, 1, False, True),
        ("game_over", GAMEBOY / "assets" / "game_over_master.png", (160, 144), (GAME_OVER_PALETTE,), None, None, False, 1, False, True),
        ("intro", GAMEBOY / "assets" / "intro_master.png", (160, 144), (INTRO_PALETTE,), None, None, False, 1, False, True),
    )):
        tiles, tilemap, attributes, preview = screen_art(path, size, palettes, crop, content_size, stretch, pixel_scale, white_background, best_palette, screen_boundary=True)
        palette_data = bytearray()
        for palette in palettes:
            for red, green, blue in palette:
                color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
                palette_data.extend((color & 255, color >> 8))
        screen_source += c_array(name + "_screen_palettes", palette_data)
        screen_source += c_array(name + "_screen_tiles", pack_tiles(tiles))
        screen_source += c_array(name + "_screen_map", tilemap)
        screen_source += c_array(name + "_screen_attributes", attributes)
        loaders.append(f"""    if (index == {index}u) {{
        {"LCDC_REG &= (uint8_t)~LCDCF_BG8000;" if name == "title" else ""}
        set_bkg_data(0u, {len(tiles)}u, {name}_screen_tiles);
        {"set_sprite_data(0u, ART_TITLE_PROMPT_TILES, title_prompt_tiles);" if name == "title" else "set_sprite_data(ART_INTRO_VERSION_BASE, ART_INTRO_VERSION_TILES, intro_version_tiles);" if name == "intro" else ""}
        set_bkg_tiles(0u, 0u, 20u, {size[1] // 8}u, {name}_screen_map);
        if (_cpu == CGB_TYPE) {{
            set_bkg_palette(0u, {len(palettes)}u, (const palette_color_t *){name}_screen_palettes);
            VBK_REG = 1u;
            set_bkg_tiles(0u, 0u, 20u, {size[1] // 8}u, {name}_screen_attributes);
            VBK_REG = 0u;
        }}
    }}""")
        preview.save(preview_dir / f"{name}.png")
    screen_source += "\nvoid art_load_screen(uint8_t index) BANKED {\n" + "\n".join(loaders) + "\n}\n"
    (GAMEBOY / "src" / "generated_screens.c").write_text(screen_source)
    credits_tiles, credits_map, credits_attributes, credits_preview = screen_art(
        make_credits_card(),
        (160, 144),
        (CREDITS_PALETTE,),
        best_palette=True,
        protected_regions=((32, 8, 128, 136),),
        protected_tile_count=len(CREDITS_FONT_GLYPH_ORDER),
        font_tiles=make_morbidosa_tiles(CREDITS_FONT_GLYPH_ORDER),
    )
    credits_palette_data = bytearray()
    for red, green, blue in CREDITS_PALETTE:
        color = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        credits_palette_data.extend((color & 255, color >> 8))
    credits_source = '#pragma bank 5\n#include <gb/gb.h>\n#include <gb/cgb.h>\n#include "generated_art.h"\n'
    credits_source += c_array("credits_screen_palettes", credits_palette_data)
    credits_source += c_array("credits_screen_tiles", pack_tiles(credits_tiles))
    credits_source += c_array("credits_screen_map", credits_map)
    credits_source += c_array("credits_screen_attributes", credits_attributes)
    credits_source += f"""
void art_load_credits_screen(void) BANKED {{
    set_bkg_data(0u, {len(credits_tiles)}u, credits_screen_tiles);
    set_sprite_data(0u, {len(CREDITS_FONT_GLYPH_ORDER)}u, credits_screen_tiles);
    set_bkg_tiles(0u, 0u, 20u, 18u, credits_screen_map);
    if (_cpu == CGB_TYPE) {{
        set_bkg_palette(0u, 1u, (const palette_color_t *)credits_screen_palettes);
        VBK_REG = 1u;
        set_bkg_tiles(0u, 0u, 20u, 18u, credits_screen_attributes);
        VBK_REG = 0u;
    }}
}}
"""
    (GAMEBOY / "src" / "generated_credits.c").write_text(credits_source)
    credits_preview.save(preview_dir / "credits.png")
    print(f"generated {len(gameplay)} gameplay tiles and {len(title)} title tiles")


if __name__ == "__main__":
    main()
