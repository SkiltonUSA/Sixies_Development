#!/usr/bin/env python3
"""Convert shared Sixies source masters to Atari ANTIC-F 1bpp assets."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re

from PIL import Image, ImageChops, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
APPLE = ROOT / "apple2" / "assets"
SHARED = ROOT / "src" / "assets"
ATARI = ROOT / "atari8"
DHGR_PAGE_BYTES = 8192
DHGR_WIDTH = 560
DHGR_HEIGHT = 192
APPLE_GRID_BOX = (127, 4, 431, 159)
ATARI_GRID_SIZE = (160, 140)
ATARI_GRID_POSITION = (80, 26)
CALLOUT_SIZE = (80, 24)
CALLOUT_FIT_SIZE = (88, 26)
C64_RGB = (
    (0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF), (0x81, 0x33, 0x38),
    (0x75, 0xCE, 0xC8), (0x8E, 0x3C, 0x97), (0x56, 0xAC, 0x4D),
    (0x2E, 0x2C, 0x9B), (0xED, 0xF1, 0x71), (0x8E, 0x50, 0x29),
    (0x55, 0x38, 0x00), (0xC4, 0x6C, 0x71), (0x4A, 0x4A, 0x4A),
    (0x7B, 0x7B, 0x7B), (0xA9, 0xFF, 0x9F), (0x70, 0x6D, 0xEB),
    (0xB2, 0xB2, 0xB2),
)


def contain(image: Image.Image, size: tuple[int, int], threshold: int = 150) -> Image.Image:
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    background = Image.new("RGBA", image.size, "white")
    image = Image.alpha_composite(background, image).convert("L")
    bbox = ImageChops.difference(image, Image.new("L", image.size, 255)).getbbox()
    if bbox:
        image = image.crop(bbox)
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("L", size, 255)
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y), alpha.crop(bbox).resize(image.size) if bbox else None)
    return canvas.point(lambda p: 255 if p < threshold else 0, mode="1")


def make_callout(image: Image.Image) -> Image.Image:
    """Invert and slightly enlarge an exclamation for the black playfield."""
    rgb = image.convert("RGB")
    intensity = ImageChops.lighter(
        ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
        rgb.getchannel("B"),
    )
    bounds = intensity.point(lambda value: 255 if value >= 16 else 0).getbbox()
    if bounds is None:
        raise ValueError("exclamation master has no visible pixels")
    detail = intensity.crop(bounds)
    detail.thumbnail(CALLOUT_FIT_SIZE, Image.Resampling.LANCZOS)
    enlarged = Image.new("L", CALLOUT_FIT_SIZE, 0)
    enlarged.paste(
        detail,
        (
            (CALLOUT_FIT_SIZE[0] - detail.width) // 2,
            (CALLOUT_FIT_SIZE[1] - detail.height) // 2,
        ),
    )
    left = (CALLOUT_FIT_SIZE[0] - CALLOUT_SIZE[0]) // 2
    top = (CALLOUT_FIT_SIZE[1] - CALLOUT_SIZE[1]) // 2
    enlarged = enlarged.crop(
        (left, top, left + CALLOUT_SIZE[0], top + CALLOUT_SIZE[1])
    )
    # Light lettering and burst pixels become Atari foreground; the masters'
    # opaque black backgrounds remain transparent against the playfield.
    return enlarged.point(lambda value: 255 if value >= 96 else 0, mode="1")


def pack_1bpp(image: Image.Image) -> bytes:
    if image.width % 8:
        raise ValueError(f"width must be byte aligned: {image.width}")
    pixels = image.convert("1")
    output = bytearray()
    for y in range(pixels.height):
        for x in range(0, pixels.width, 8):
            value = 0
            for bit in range(8):
                if pixels.getpixel((x + bit, y)):
                    value |= 0x80 >> bit
            output.append(value)
    return bytes(output)


def pack_rle(data: bytes) -> bytes:
    """Pack bytes as 1-128 byte literal/repeat packets for the 6502 decoder."""
    output = bytearray()
    index = 0
    while index < len(data):
        repeat = 1
        while (
            index + repeat < len(data)
            and repeat < 128
            and data[index + repeat] == data[index]
        ):
            repeat += 1
        if repeat >= 3:
            output.extend((0x80 | (repeat - 1), data[index]))
            index += repeat
            continue

        literal_start = index
        index += repeat
        while index < len(data) and index - literal_start < 128:
            next_repeat = 1
            while (
                index + next_repeat < len(data)
                and next_repeat < 128
                and data[index + next_repeat] == data[index]
            ):
                next_repeat += 1
            if next_repeat >= 3:
                break
            index += min(next_repeat, 128 - (index - literal_start))
        literal = data[literal_start:index]
        output.append(len(literal) - 1)
        output.extend(literal)
    return bytes(output)


def unpack_rle(data: bytes) -> bytes:
    """Host-side decoder used to verify every generated packed screen."""
    output = bytearray()
    index = 0
    while index < len(data):
        packet = data[index]
        index += 1
        count = (packet & 0x7F) + 1
        if packet & 0x80:
            if index >= len(data):
                raise ValueError("truncated RLE repeat packet")
            output.extend(bytes((data[index],)) * count)
            index += 1
        else:
            if index + count > len(data):
                raise ValueError("truncated RLE literal packet")
            output.extend(data[index : index + count])
            index += count
    return bytes(output)


def physical_screen(image: Image.Image) -> bytes:
    """Expand a bitmap to the 31 physical pages reserved for ANTIC video."""
    if image.size != (320, 192):
        raise ValueError(f"full screen must be 320x192, got {image.size}")
    logical = pack_1bpp(image)
    # ANTIC restarts at $9000 after row 99. Fill both that 96-byte boundary
    # gap and the 160 bytes after row 191, matching clear_screen's 31 pages.
    return logical[:4000] + bytes(96) + logical[4000:] + bytes(160)


def save_rle_screen(image: Image.Image, binary: Path, preview: Path) -> None:
    physical = physical_screen(image)
    packed = pack_rle(physical)
    if unpack_rle(packed) != physical:
        raise ValueError(f"RLE verification failed for {binary.name}")
    binary.write_bytes(packed)
    preview.parent.mkdir(parents=True, exist_ok=True)
    ImageOps.invert(image.convert("L")).save(preview)


def save_asset(image: Image.Image, binary: Path, preview: Path) -> None:
    binary.write_bytes(pack_1bpp(image))
    preview.parent.mkdir(parents=True, exist_ok=True)
    ImageOps.invert(image.convert("L")).save(preview)


def hgr_offset(y: int) -> int:
    """Return the byte offset for a scanline in an Apple II HGR/DHGR page."""
    return ((y & 0x07) << 10) + (((y >> 3) & 0x07) << 7) + (y >> 6) * 0x28


def decode_a2fm_title() -> Image.Image:
    """Decode and verify the supplied b2d A2FM title as a 560x192 bitmap."""
    source = (APPLE / "title_dhgr_mono_master.a2fm").read_bytes()
    if len(source) != DHGR_PAGE_BYTES * 2:
        raise ValueError("A2FM title must contain one 8K auxiliary and one 8K main page")

    # b2d stores the complete auxiliary page before the complete main page.
    auxiliary = source[:DHGR_PAGE_BYTES]
    main = source[DHGR_PAGE_BYTES:]
    image = Image.new("L", (DHGR_WIDTH, DHGR_HEIGHT), 0)
    pixels = image.load()
    for y in range(DHGR_HEIGHT):
        row = hgr_offset(y)
        x = 0
        for byte_index in range(40):
            for bank in (auxiliary, main):
                value = bank[row + byte_index]
                for bit in range(7):
                    pixels[x, y] = 255 if value & (1 << bit) else 0
                    x += 1

    with Image.open(APPLE / "title_dhgr_mono_reference.png") as reference:
        if reference.size != (DHGR_WIDTH, DHGR_HEIGHT * 2):
            raise ValueError("DHGR title reference must be 560x384")
        expected = reference.convert("L").point(lambda value: 255 if value >= 128 else 0)
        doubled = image.resize(expected.size, Image.Resampling.NEAREST)
        if doubled.tobytes() != expected.tobytes():
            raise ValueError("decoded A2FM title does not match its reference PNG")
    return image


def decode_a2fm_grid_screen() -> Image.Image:
    """Decode and verify the supplied complete Apple DHGR game composition."""
    source = (APPLE / "game_grid_dhgr_mono_master.a2fm").read_bytes()
    if len(source) != DHGR_PAGE_BYTES * 2:
        raise ValueError(
            "A2FM game grid must contain one 8K auxiliary and one 8K main page"
        )

    auxiliary = source[:DHGR_PAGE_BYTES]
    main = source[DHGR_PAGE_BYTES:]
    image = Image.new("L", (DHGR_WIDTH, DHGR_HEIGHT), 0)
    pixels = image.load()
    for y in range(DHGR_HEIGHT):
        row = hgr_offset(y)
        x = 0
        for byte_index in range(40):
            for bank in (auxiliary, main):
                value = bank[row + byte_index]
                for bit in range(7):
                    pixels[x, y] = 255 if value & (1 << bit) else 0
                    x += 1

    with Image.open(APPLE / "game_grid_dhgr_mono_reference.png") as reference:
        if reference.size != (DHGR_WIDTH, DHGR_HEIGHT * 2):
            raise ValueError("DHGR game-grid reference must be 560x384")
        expected = reference.convert("L").point(lambda value: 255 if value >= 128 else 0)
        doubled = image.resize(expected.size, Image.Resampling.NEAREST)
        if doubled.tobytes() != expected.tobytes():
            raise ValueError("decoded A2FM game grid does not match its reference PNG")

    # The separately supplied high-resolution PNG is the artwork master. Its
    # presence and geometry are checked here while the already-dithered DHGR
    # crop below supplies the most legible decorative joints at 320x192.
    with Image.open(APPLE / "grid_master.png") as master:
        if master.size != (1254, 1254):
            raise ValueError("high-resolution grid master must be 1254x1254")
        rgb = master.convert("RGB")
        intensity = ImageChops.lighter(
            ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
            rgb.getchannel("B"),
        )
        visible = intensity.point(lambda value: 255 if value >= 24 else 0)
        if visible.getbbox() is None:
            raise ValueError("high-resolution grid master has no visible artwork")
    return image


def make_atari_grid_screen() -> Image.Image:
    """Place the Apple 5x5 grid in the Atari playfield's exact cell geometry."""
    apple_screen = decode_a2fm_grid_screen()
    grid = apple_screen.crop(APPLE_GRID_BOX).resize(
        ATARI_GRID_SIZE, Image.Resampling.NEAREST
    )
    screen = Image.new("1", (320, 192), 0)
    screen.paste(grid, ATARI_GRID_POSITION)
    screen.paste(make_game_logo(), (80, 1))
    return screen


def make_atari_title() -> Image.Image:
    """Convert the supplied flat Sixies title to an ANTIC-F composition."""
    with Image.open(ATARI / "assets" / "title_master.png") as source:
        if source.size != (256, 240):
            raise ValueError("Atari title master must be the supplied 256x240 image")
        rgb = source.convert("RGB")

    # Taking the brightest channel retains each saturated mascot and letter
    # color when reduced to monochrome. 196x147 compensates for ANTIC-F's
    # narrow NTSC pixels while leaving two unobstructed text rows below it.
    intensity = ImageChops.lighter(
        ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
        rgb.getchannel("B"),
    )
    title = intensity.resize((196, 147), Image.Resampling.LANCZOS)
    return title.point(lambda value: 255 if value >= 128 else 0, mode="1")


def make_game_logo() -> Image.Image:
    """Center the supplied Sixies master in the strip above the game grid."""
    with Image.open(ATARI / "assets" / "game_logo_master.png") as source:
        if source.size != (1983, 793):
            raise ValueError("gameplay logo must be the supplied 1983x793 master")
        rgb = source.convert("RGB")

    intensity = ImageChops.lighter(
        ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
        rgb.getchannel("B"),
    )
    visible = intensity.point(lambda value: 255 if value >= 24 else 0)
    bounds = visible.getbbox()
    if bounds is None:
        raise ValueError("gameplay logo master has no visible pixels")
    logo = intensity.crop(bounds)
    logo.thumbnail((152, 24), Image.Resampling.LANCZOS)
    canvas = Image.new("L", (160, 24), 0)
    canvas.paste(logo, ((160 - logo.width) // 2, (24 - logo.height) // 2))
    return canvas.point(lambda value: 255 if value >= 108 else 0, mode="1")


def make_atari_presentation(path: Path) -> Image.Image:
    """Fit light-on-black Apple presentation art into a 240x120 Atari panel."""
    with Image.open(path) as source:
        rgb = source.convert("RGB")
    intensity = ImageChops.lighter(
        ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
        rgb.getchannel("B"),
    )
    bounds = intensity.point(lambda value: 255 if value >= 24 else 0).getbbox()
    if bounds is None:
        raise ValueError(f"presentation artwork has no visible pixels: {path}")
    fitted = ImageOps.contain(
        intensity.crop(bounds), (240, 120), Image.Resampling.LANCZOS
    )
    canvas = Image.new("L", (240, 120), 0)
    canvas.paste(fitted, ((240 - fitted.width) // 2, (120 - fitted.height) // 2))
    return canvas.convert("1", dither=Image.Dither.FLOYDSTEINBERG)


def make_panel_screen(panel: Image.Image, y: int = 36) -> Image.Image:
    """Center a 240-pixel panel on a complete ANTIC-F screen."""
    if panel.size != (240, 120):
        raise ValueError(f"expected 240x120 panel, got {panel.size}")
    screen = Image.new("1", (320, 192), 0)
    screen.paste(panel, (40, y))
    return screen


def make_art_screen(art: Image.Image, position: tuple[int, int]) -> Image.Image:
    """Place arbitrary monochrome art on a complete ANTIC-F screen."""
    screen = Image.new("1", (320, 192), 0)
    screen.paste(art, position)
    return screen


def load_apple_instruction_generator():
    """Load the supplied Apple screen generator as the design/font contract."""
    path = ROOT / "apple2" / "scripts" / "generate_instructions.py"
    spec = importlib.util.spec_from_file_location("sixies_apple_instructions", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load Apple instruction generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_atari_instructions() -> Image.Image:
    """Rebuild the supplied boxed Apple instructions for a 320px Atari screen."""
    apple = load_apple_instruction_generator()
    reference = apple.render_instructions()
    if reference.size != (560, 192) or reference.getbbox() is None:
        raise ValueError("supplied Apple instruction design did not render correctly")

    image = Image.new("1", (320, 192), 0)
    pixels = image.load()

    def text(line: str, y: int) -> None:
        cell_width = 7
        width = len(line) * cell_width - 2
        x = (image.width - width) // 2
        for character in line:
            if character not in apple.FONT:
                raise ValueError(f"instruction font has no {character!r}")
            for row, bits in enumerate(apple.FONT[character]):
                for column in range(5):
                    if bits & (1 << (4 - column)):
                        pixels[x + column, y + row] = 1
            x += cell_width

    draw = ImageDraw.Draw(image)

    def double_box(left: int, top: int, right: int, bottom: int) -> None:
        draw.rectangle((left, top, right, bottom), outline=1)
        draw.rectangle((left + 2, top + 2, right - 2, bottom - 2), outline=1)

    double_box(8, 4, 311, 27)
    text("SIXIES ATARI 8-BIT  (C) 2026 D. SKILTON", 8)
    text("BUILT FOR 64K AND 128K XL XE", 17)

    double_box(94, 33, 225, 48)
    text("HOW TO PLAY", 38)

    rules = (
        "PLACE ONE OR TWO DICE ON THE 5 X 5 GRID.",
        "MATCH 3 EDGE-TOUCHING DICE OF SAME VALUE.",
        "THEY MERGE INTO THE NEXT NUMBER.",
        "THREE SIXES CLEAR FOR A 50 POINT BONUS.",
        "CHAIN REACTIONS BUILD YOUR SCORE.",
        "A FULL GRID ENDS THE GAME.",
    )
    for index, line in enumerate(rules):
        text(line, 55 + index * 10)

    double_box(8, 116, 311, 160)
    text("CONTROLS", 121)
    controls = (
        "WASD OR JOYSTICK MOVE   Q OR E ROTATE",
        "SPACE RETURN OR FIRE PLACE   N NEW GAME",
        "[M] SOUND   [I] INSTRUCTIONS",
    )
    for index, line in enumerate(controls):
        text(line, 131 + index * 9)

    double_box(68, 169, 251, 188)
    text("FIRE OR SPACE TO CONTINUE", 175)
    return image


def load_acme_die(path: Path) -> Image.Image:
    """Load an attached ACME 24x20 sprite and center it in a 32x24 cell."""
    values = [
        int(value, 16)
        for value in re.findall(r"\$([0-9a-fA-F]{2})(?![0-9a-fA-F])", path.read_text())
    ]
    # Each supplied file has 60 visible bytes and four C64-style padding bytes.
    if len(values) != 64 or values[60:] != [0, 0, 0, 0]:
        raise ValueError(f"expected 60 sprite bytes plus four zero bytes: {path}")
    image = Image.new("1", (32, 24), 0)
    pixels = image.load()
    for y in range(20):
        row = values[y * 3 : y * 3 + 3]
        for x in range(24):
            if row[x // 8] & (0x80 >> (x & 7)):
                pixels[x + 4, y + 2] = 1
    return image


def load_merge_star() -> Image.Image:
    """Load the shared C64 four-point merge star into one Atari die cell."""
    path = SHARED / "merge_firework_sprite.asm"
    values = [
        int(value, 16)
        for value in re.findall(r"\$([0-9a-fA-F]{2})(?![0-9a-fA-F])", path.read_text())
    ]
    if len(values) != 64 or values[-1] != 0:
        raise ValueError("expected 63 merge-star bytes plus one zero padding byte")
    image = Image.new("1", (32, 24), 0)
    pixels = image.load()
    for y in range(21):
        row = values[y * 3 : y * 3 + 3]
        for x in range(24):
            if row[x // 8] & (0x80 >> (x & 7)):
                pixels[x + 4, y + 1] = 1
    return image


def c64_luma(color: int) -> int:
    red, green, blue = C64_RGB[color & 0x0F]
    return 299 * red + 587 * green + 114 * blue


def load_c64_mascot() -> Image.Image:
    """Reconstruct the supplied 64x80 C64 bitmap using its color-cell map."""
    metadata = (SHARED / "main_mascot.asm").read_text()
    expected_bins = {"main_mascot_bitmap.bin", "main_mascot_screen.bin"}
    referenced_bins = set(re.findall(r'!bin "src/assets/([^"]+)"', metadata))
    if referenced_bins != expected_bins:
        raise ValueError("main mascot metadata does not reference the expected bitmap and screen files")

    bitmap = (SHARED / "main_mascot_bitmap.bin").read_bytes()
    screen = (SHARED / "main_mascot_screen.bin").read_bytes()
    if len(bitmap) != 640 or len(screen) != 80:
        raise ValueError("expected a 640-byte bitmap and an 80-byte screen map")

    image = Image.new("1", (64, 80), 0)
    pixels = image.load()
    for cell_y in range(10):
        for cell_x in range(8):
            colors = screen[cell_y * 8 + cell_x]
            background = colors & 0x0F
            foreground = colors >> 4
            background_luma = c64_luma(background)
            foreground_luma = c64_luma(foreground)
            same_visible_color = background == foreground and background != 0
            for row in range(8):
                source = bitmap[cell_y * 64 + cell_x * 8 + row]
                for bit in range(8):
                    selected_foreground = bool(source & (0x80 >> bit))
                    if same_visible_color or (
                        selected_foreground and foreground_luma > background_luma
                    ) or (
                        not selected_foreground and background_luma > foreground_luma
                    ):
                        pixels[cell_x * 8 + bit, cell_y * 8 + row] = 1
    return image


def load_detailed_mascot() -> Image.Image:
    """Reduce the compact high-score mascot master to the 80x100 sidebar."""
    with Image.open(ATARI / "assets" / "high_score_mascot_master.png") as source:
        if source.size != (1122, 1402):
            raise ValueError("high-score mascot master must be the supplied 1122x1402 image")
        rgb = source.convert("RGB")
    intensity = ImageChops.lighter(
        ImageChops.lighter(rgb.getchannel("R"), rgb.getchannel("G")),
        rgb.getchannel("B"),
    )
    bounds = intensity.point(lambda value: 255 if value >= 16 else 0).getbbox()
    if bounds is None:
        raise ValueError("Atari mascot master has no visible pixels")

    # The edited master already uses chunky one-bit contours and a compact 4:5
    # pose. LANCZOS plus a high threshold preserves its face, dice, and shoes.
    detail = intensity.crop(bounds)
    detail.thumbnail((80, 100), Image.Resampling.LANCZOS)
    canvas = Image.new("L", (80, 100), 0)
    canvas.paste(detail, ((80 - detail.width) // 2, (100 - detail.height) // 2))
    return canvas.point(lambda value: 255 if value >= 144 else 0, mode="1")


def unpack_exclamation(data: bytes, start: int, end: int) -> bytes:
    """Decode the C64 zero-run/literal stream into three 24x21 sprites."""
    output = bytearray()
    index = start
    while len(output) < 189:
        if index >= end:
            raise ValueError("truncated exclamation sprite stream")
        packet = data[index]
        index += 1
        count = packet & 0x7F
        if not count:
            raise ValueError("zero-length exclamation packet")
        if packet & 0x80:
            output.extend(b"\0" * count)
        else:
            if index + count > end:
                raise ValueError("literal exclamation packet crosses its offset boundary")
            output.extend(data[index : index + count])
            index += count
    if len(output) != 189 or index != end:
        raise ValueError("exclamation stream did not decode to exactly three sprites")
    return bytes(output)


def exclamation_image(sprite_data: bytes) -> Image.Image:
    """Join three C64 24x21 sprites and center them in an Atari 80x24 banner."""
    if len(sprite_data) != 189:
        raise ValueError("expected three 63-byte C64 sprites")
    image = Image.new("1", (80, 24), 0)
    pixels = image.load()
    for sprite in range(3):
        sprite_offset = sprite * 63
        for y in range(21):
            row = sprite_data[sprite_offset + y * 3 : sprite_offset + y * 3 + 3]
            for x in range(24):
                if row[x // 8] & (0x80 >> (x & 7)):
                    pixels[4 + sprite * 24 + x, 1 + y] = 1
    return image


def load_exclamation_images() -> dict[str, Image.Image]:
    metadata = (SHARED / "exclamation_sprites_data.asm").read_text()
    offsets = [int(value) for value in re.findall(r"ExclamationSpriteData \+ (\d+)", metadata)]
    # The low and high tables repeat the six offsets; use one table only.
    if len(offsets) != 12 or offsets[:6] != offsets[6:]:
        raise ValueError("invalid exclamation offset tables")
    offsets = offsets[:6]
    data = (SHARED / "exclamation_sprites.bin").read_bytes()
    boundaries = offsets[1:] + [len(data)]
    names = ("yay", "wow", "boom", "fives", "sixies", "awesome")
    return {
        name: exclamation_image(unpack_exclamation(data, start, end))
        for name, start, end in zip(names, offsets, boundaries)
    }


def make_occupied_shade() -> Image.Image:
    """Build the clipped diagonal hatch used over an occupied board cell."""
    image = Image.new("1", (32, 24), 0)
    pixels = image.load()
    for y in range(2, 22):
        for x in range(4, 28):
            if (x + y) % 8 < 3:
                pixels[x, y] = 1
    return image


def build(output: Path, previews: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    previews.mkdir(parents=True, exist_ok=True)

    title = make_art_screen(make_atari_title(), (62, 0))
    save_rle_screen(title, output / "title_logo.rle", previews / "title_logo.png")

    presents = make_panel_screen(make_atari_presentation(APPLE / "presents_master.ppm"))
    save_rle_screen(presents, output / "presents.rle", previews / "presents.png")

    instructions = make_atari_instructions()
    save_rle_screen(
        instructions, output / "instructions.rle", previews / "instructions.png"
    )

    game_over = make_art_screen(
        make_atari_presentation(APPLE / "game_over_master.png"), (40, 20)
    )
    save_rle_screen(game_over, output / "game_over.rle", previews / "game_over.png")

    grid = make_atari_grid_screen()
    save_rle_screen(grid, output / "game_grid.rle", previews / "game_grid.png")

    # Decode the supplied C64 bitmap and screen data as a build-time integrity
    # check, then render the supplied Atari-specific monochrome mascot master.
    load_c64_mascot()
    mascot = load_detailed_mascot()
    save_asset(mascot, output / "mascot.bin", previews / "mascot.png")

    dice = bytearray()
    dice_preview = Image.new("1", (32 * 6, 24), 0)
    die_names = ("one", "two", "three", "four", "five", "six")
    for value, name in enumerate(die_names, 1):
        die = load_acme_die(ATARI / "assets" / "dice" / f"die_{name}.asm")
        dice.extend(pack_1bpp(die))
        dice_preview.paste(die, ((value - 1) * 32, 0))
    (output / "dice.bin").write_bytes(dice)
    ImageOps.invert(dice_preview.convert("L")).save(previews / "dice.png")

    invalid = Image.new("1", (32, 24), 0)
    draw = ImageDraw.Draw(invalid)
    draw.line((4, 2, 27, 21), fill=1, width=2)
    draw.line((27, 2, 4, 21), fill=1, width=2)
    save_asset(invalid, output / "invalid.bin", previews / "invalid.png")

    occupied = make_occupied_shade()
    save_asset(
        occupied, output / "occupied.bin", previews / "occupied.png"
    )

    merge_star = load_merge_star()
    save_asset(
        merge_star, output / "merge_star.bin", previews / "merge_star.png"
    )

    callout_names = (
        "awesome", "boom", "dang", "fives", "lets_go",
        "sixies", "whoa", "wow", "yeah", "yes",
    )
    # Decode the earlier packed C64 banners as a build-time integrity check,
    # but render all ten official words from their high-resolution masters.
    # The newly supplied PNGs are byte-identical to the Apple previews made
    # from these masters, so this preserves their exact named slot order.
    load_exclamation_images()
    callouts = bytearray()
    atlas = Image.new("1", (80, 24 * len(callout_names)), 0)
    for index, name in enumerate(callout_names):
        art = make_callout(Image.open(APPLE / f"merge_{name}_master.png"))
        callouts.extend(pack_1bpp(art))
        atlas.paste(art, (0, index * 24))
    (output / "callouts.bin").write_bytes(callouts)
    atlas.convert("L").save(previews / "callouts.png")

    font_source = SHARED / "font" / "SixiesFont_charset.bin"
    screen_font = font_source.read_bytes()
    if len(screen_font) != 512:
        raise ValueError(f"expected 512-byte C64 screen-code font, got {len(screen_font)}")
    # Expand the C64 screen-code layout into direct ASCII indexing so the
    # Atari renderer can multiply an ASCII byte by eight without a map table.
    # Every game string and custom renderer glyph is below ASCII $80, so a
    # 128-glyph direct-index table retains the fast 6502 lookup while freeing
    # 1K of the very tight 64K build.
    font = bytearray(1024)
    footer_glyphs = {
        1: (0xFF, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00),
        2: (0x0F, 0x30, 0x40, 0x80, 0x80, 0x80, 0x80, 0x80),
        3: (0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
        4: (0xF0, 0x0C, 0x02, 0x01, 0x01, 0x01, 0x01, 0x01),
        5: (0x80, 0x80, 0x80, 0x80, 0x80, 0x40, 0x30, 0x0F),
        6: (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF),
        7: (0x01, 0x01, 0x01, 0x01, 0x01, 0x02, 0x0C, 0xF0),
    }
    for character, glyph in footer_glyphs.items():
        font[character * 8 : (character + 1) * 8] = bytes(glyph)
    font[ord("!") * 8 : (ord("!") + 1) * 8] = screen_font[8:16]
    font[ord("[") * 8 : (ord("[") + 1) * 8] = bytes(
        (0x3C, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x3C)
    )
    font[ord("]") * 8 : (ord("]") + 1) * 8] = bytes(
        (0x3C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x3C)
    )
    font[ord(".") * 8 : (ord(".") + 1) * 8] = bytes(
        (0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18, 0x00)
    )
    font[ord(">") * 8 : (ord(">") + 1) * 8] = bytes(
        (0x40, 0x20, 0x10, 0x08, 0x10, 0x20, 0x40, 0x00)
    )
    for digit in range(10):
        source = (16 + digit) * 8
        target = (ord("0") + digit) * 8
        font[target : target + 8] = screen_font[source : source + 8]
    for letter in range(26):
        source = (33 + letter) * 8
        target = (ord("A") + letter) * 8
        font[target : target + 8] = screen_font[source : source + 8]
    (output / "font.bin").write_bytes(font)

    manifest = (
        f"title_logo.rle {len(pack_rle(physical_screen(title)))} bytes, 320x192 PackBits RLE\n"
        f"presents.rle {len(pack_rle(physical_screen(presents)))} bytes, 320x192 PackBits RLE\n"
        f"instructions.rle {len(pack_rle(physical_screen(instructions)))} bytes, 320x192 PackBits RLE\n"
        f"game_over.rle {len(pack_rle(physical_screen(game_over)))} bytes, 320x192 PackBits RLE\n"
        f"game_grid.rle {len(pack_rle(physical_screen(grid)))} bytes, 320x192 PackBits RLE\n"
        "mascot.bin 80x100 1bpp (compact high-score mascot master)\n"
        "dice.bin 6x(32x24) 1bpp\n"
        "invalid.bin 32x24 1bpp\n"
        "occupied.bin 32x24 1bpp (diagonal occupied-cell shade)\n"
        "merge_star.bin 32x24 1bpp (shared C64 four-point star)\n"
        "callouts.bin 10x(80x24) 1bpp\n"
        "font.bin 128x(8x8) 1bpp\n"
    )
    (output / "MANIFEST.txt").write_text(manifest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previews", type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.previews)


if __name__ == "__main__":
    main()
