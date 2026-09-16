from io import BytesIO
from pathlib import Path
import re

from pyboy import PyBoy
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
with Image.open(ROOT / "assets/font_lanky_master.png") as atlas:
    LANKY_ATLAS = atlas.convert("RGB")
LANKY_GLYPHS = {}
for codepoint in range(32, 127):
    atlas_index = codepoint - 32
    glyph = Image.new("L", (8, 8))
    glyph.putdata([3 if pixel in ((0, 0, 0), (7, 24, 33)) else 0 for pixel in LANKY_ATLAS.crop((atlas_index % 16 * 8, atlas_index // 16 * 8, atlas_index % 16 * 8 + 8, atlas_index // 16 * 8 + 8)).getdata()])
    bounds = glyph.getbbox()
    LANKY_GLYPHS[chr(codepoint)] = glyph.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (2, 8))
with Image.open(ROOT / "assets/font_itty_bitty_master.png") as atlas:
    SMALL_ATLAS = atlas.convert("RGB")
HIGHSCORE_GLYPHS = {}
for character in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ /:.+!":
    atlas_index = ord(character) - 32
    glyph = Image.new("L", (8, 8))
    glyph.putdata([3 if pixel == (224, 248, 207) else 0 for pixel in SMALL_ATLAS.crop((atlas_index % 16 * 8, atlas_index // 16 * 8, atlas_index % 16 * 8 + 8, atlas_index // 16 * 8 + 8)).getdata()])
    bounds = glyph.getbbox()
    HIGHSCORE_GLYPHS[character] = glyph.crop((bounds[0], 0, bounds[2], 8)) if bounds else Image.new("L", (2, 8))
INSTRUCTION_SOURCE = (ROOT / "src/generated_instructions.c").read_text()
INSTRUCTION_MAPS = [int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", INSTRUCTION_SOURCE.split("const uint8_t instruction_maps[] = {", 1)[1].split("};", 1)[0])]
INSTRUCTION_PAGES = len(INSTRUCTION_MAPS) // 360
NEXT_SOURCE = (ROOT / "src/generated_board.c").read_text().split("const uint8_t gameplay_next_frame[] = {", 1)[1].split("};", 1)[0]
NEXT_FRAME = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", NEXT_SOURCE))
INVALID_SOURCE = (ROOT / "src/generated_callouts.c").read_text()
INVALID_MAP = [int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", INVALID_SOURCE.split("const uint8_t invalid_next_map[] = {", 1)[1].split("};", 1)[0])]
INVALID_BYTES = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", INVALID_SOURCE.split("const uint8_t invalid_next_tiles[] = {", 1)[1].split("};", 1)[0]))
START_MENU_SOURCE = (ROOT / "src/generated_start_menu.c").read_text()
START_MENU_MAP = [int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", START_MENU_SOURCE.split("const uint8_t start_menu_map[] = {", 1)[1].split("};", 1)[0])]
ART_HEADER = (ROOT / "include/generated_art.h").read_text()
SCORE_BASE = int(re.search(r"#define ART_SCORE_PANEL_BASE (\d+)u", ART_HEADER).group(1))
TITLE_PROMPT_TILES = int(re.search(r"#define ART_TITLE_PROMPT_TILES (\d+)u", ART_HEADER).group(1))
INTRO_VERSION_BASE = int(re.search(r"#define ART_INTRO_VERSION_BASE (\d+)u", ART_HEADER).group(1))
INTRO_VERSION_DIGIT_BASE = INTRO_VERSION_BASE + 2
BUILD_VERSION = int(re.search(r"#define SIXIES_BUILD_VERSION (\d+)UL", (ROOT / "include/build_version.h").read_text()).group(1))
GAMEPLAY_ART_SOURCE = (ROOT / "src/generated_art.c").read_text()
SCORE_POPUP_DIGITS = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", GAMEPLAY_ART_SOURCE.split("const uint8_t score_popup_digits[] = {", 1)[1].split("};", 1)[0]))
CALLOUT_DATA = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", INVALID_SOURCE.split("const uint8_t callout_tiles[] = {", 1)[1].split("};", 1)[0]))
CALLOUT_BASE = int(re.search(r"#define ART_CALLOUT_BASE (\d+)u", ART_HEADER).group(1))
CALLOUT_TILES = int(re.search(r"#define ART_CALLOUT_TILES (\d+)u", ART_HEADER).group(1))
CALLOUT_SPRITES = int(re.search(r"#define ART_CALLOUT_SPRITES (\d+)u", ART_HEADER).group(1))
CALLOUT_WIDTH = int(re.search(r"#define ART_CALLOUT_SPRITE_WIDTH (\d+)u", ART_HEADER).group(1))
CALLOUT_IMAGES = {CALLOUT_DATA[offset:offset + CALLOUT_TILES * 16] for offset in range(0, len(CALLOUT_DATA), CALLOUT_TILES * 16)}
GAME_MASCOT_BASE = int(re.search(r"#define ART_GAME_MASCOT_BASE (\d+)u", ART_HEADER).group(1))
GAME_MASCOT_WIDTH = int(re.search(r"#define ART_GAME_MASCOT_WIDTH (\d+)u", ART_HEADER).group(1))
GAME_MASCOT_HEIGHT = int(re.search(r"#define ART_GAME_MASCOT_HEIGHT (\d+)u", ART_HEADER).group(1))
GAME_MASCOT_TILES = int(re.search(r"#define ART_GAME_MASCOT_TILES (\d+)u", ART_HEADER).group(1))
GAME_MASCOT_SOURCE = GAMEPLAY_ART_SOURCE.split("const uint8_t game_mascot_tiles[] = {", 1)[1].split("};", 1)[0]
GAME_MASCOT_BYTES = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", GAME_MASCOT_SOURCE))
CHAIN_REACTION_BASE = int(re.search(r"#define ART_CHAIN_REACTION_BASE (\d+)u", ART_HEADER).group(1))
CHAIN_REACTION_TILES = int(re.search(r"#define ART_CHAIN_REACTION_TILES (\d+)u", ART_HEADER).group(1))
CHAIN_REACTION_SPRITES = int(re.search(r"#define ART_CHAIN_REACTION_SPRITES (\d+)u", ART_HEADER).group(1))
CHAIN_REACTION_SOURCE = INVALID_SOURCE.split("const uint8_t chain_reaction_tiles[] = {", 1)[1].split("};", 1)[0]
CHAIN_REACTION_BYTES = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", CHAIN_REACTION_SOURCE))
BOARD_BASE = int(re.search(r"#define ART_BOARD_BASE (\d+)u", ART_HEADER).group(1))
BOARD_TILES = int(re.search(r"#define ART_BOARD_TILES (\d+)u", ART_HEADER).group(1))
assert re.search(r"#define ART_CELL_PIXELS 20u\b", ART_HEADER), "cardinal rule: grid squares must remain 20x20 pixels"
NEXT_DICE_BASE = int(re.search(r"#define ART_NEXT_DICE_BASE (\d+)u", ART_HEADER)[1])
BOARD_TILE_WIDTH = int(re.search(r"#define ART_BOARD_TILE_WIDTH (\d+)u", ART_HEADER)[1])
assert BOARD_BASE + BOARD_TILES == 224, "board canvas must not overlap callouts"
assert CHAIN_REACTION_BASE + CHAIN_REACTION_TILES <= BOARD_BASE, "chain badge must use reserved OBJ VRAM"
NEXT_VRAM = 0x9000 + NEXT_DICE_BASE * 16
assert re.search(r"#define ART_DICE_PIXELS 18u\b", ART_HEADER), "board and preview dice canvases must remain 18x18 pixels"
SYMBOLS = {}
for line in (ROOT / "build/sixies.sym").read_text().splitlines():
    match = re.fullmatch(r"[0-9A-Fa-f]+:([0-9A-Fa-f]+) (\S+)", line)
    if match:
        SYMBOLS[match[2]] = int(match[1], 16)


def press(emulator, button, frames=3):
    emulator.button_press(button)
    emulator.tick(frames)
    emulator.button_release(button)
    emulator.tick(5)


def wait_screen(emulator, screen, limit=400):
    for _ in range(limit):
        if emulator.memory[SYMBOLS["_screen_state"]] == screen:
            emulator.tick(12)
            if emulator.memory[0xFF40] & 0x80:
                emulator.tick(2)
                return
        emulator.tick()
    raise AssertionError(f"screen {screen} never reached; got {emulator.memory[SYMBOLS['_screen_state']]}")


def wait_sprites(emulator, visible, limit=100):
    for _ in range(limit):
        if bool(emulator.memory[0xFF40] & 0x02) == visible:
            return
        emulator.tick()
    raise AssertionError(f"sprites never became {'visible' if visible else 'hidden'}")


def title_prompt_visible(emulator):
    return any(emulator.memory[0xFE00 + index * 4] == 132 for index in range(TITLE_PROMPT_TILES))


def wait_title_prompt(emulator, visible, limit=100):
    for _ in range(limit):
        if title_prompt_visible(emulator) == visible:
            return
        emulator.tick()
    raise AssertionError(f"title prompt never became {'visible' if visible else 'hidden'}")


def boot(cgb, ram=None):
    emulator = PyBoy(BytesIO((ROOT / "build/sixies.gb").read_bytes()), ram_file=BytesIO(ram) if ram else None, window="null", cgb=cgb, sound_sample_rate=48000)
    emulator.set_emulation_speed(0)
    if not cgb:
        emulator.hook_register(0, 0x100, lambda _: setattr(emulator.register_file, "A", 1), None)
    emulator.tick(180)
    return emulator


def saved_ram(emulator):
    emulator.memory[0] = 0x0A
    emulator.memory[0x4000] = 0
    data = bytes(emulator.memory[0xA000:0xC000])
    emulator.memory[0] = 0
    return data


def static_gameplay_art(emulator):
    assert not emulator.memory[0xFF40] & 0x10, "gameplay lost signed background addressing"
    return bytes(
        emulator.memory[0x9000 + (tile if tile < 128 else tile - 256) * 16 + offset]
        for tile in (*range(SCORE_BASE), 255)
        if not BOARD_BASE <= tile < BOARD_BASE + BOARD_TILES
        if not NEXT_DICE_BASE <= tile < NEXT_DICE_BASE + 32
        for offset in range(16)
    )


def check_game_mascot(emulator, cgb):
    for sprite in range(10, 40):
        assert emulator.memory[0xFE00 + sprite * 4] == 0, "gameplay mascot sprite is still visible"


def check_title_prompt(emulator, background):
    with Image.open(ROOT / "assets/fonts/morbidosa/Morbidosa_avr.bmp") as master:
        atlas = master.convert("L")
    screen = emulator.screen.image
    ink = screen.getpixel((0, 0))
    phrase = "Press Start"
    for row in range(144):
        for column in range(160):
            expected = background.getpixel((column, row))
            if 116 <= row < 124 and 36 <= column < 124:
                character = phrase[(column - 36) // 8]
                codepoint = ord(character) + 96
                if atlas.getpixel(((codepoint % 16) * 8 + (column - 36) % 8, (codepoint // 16) * 8 + row - 116)):
                    expected = ink
            assert screen.getpixel((column, row)) == expected, f"Morbidosa prompt changed or displaced pixels at {column},{row}"
    assert sum(emulator.memory[0xFE00 + index * 4] == 132 for index in range(40)) == TITLE_PROMPT_TILES, "title exceeds ten sprites per scanline"


def check_intro_version(emulator):
    version = f"V{BUILD_VERSION // 100}.{BUILD_VERSION % 100:02d}"
    vertical_offset = 136 if len(version) > 10 else 144
    for index, character in enumerate(version):
        offset = 0 if character == "V" else 1 if character == "." else 2 + int(character)
        sprite = INTRO_VERSION_BASE + index
        address = 0xFE00 + sprite * 4
        assert emulator.memory[address] == vertical_offset + (index // 10) * 8, "intro version has the wrong vertical position"
        assert emulator.memory[address + 1] == 12 + (index % 10) * 8, "intro version has the wrong horizontal position"
        assert emulator.memory[address + 2] == INTRO_VERSION_BASE + offset, "intro version glyph is incorrect"


def check_screen_boundary(emulator):
    screen = emulator.screen.image
    border = screen.getpixel((0, 0))
    if emulator.memory[SYMBOLS["_screen_state"]] == 4:
        assert border[:3] == (0, 0, 0), "gameplay screen boundary is not pure black"
        check_gameplay_background(emulator)
    assert border != screen.getpixel((1, 1)), "screen boundary is not visible"
    assert all(screen.getpixel((column, row)) == border for row in (0, 143) for column in range(160)), "top or bottom screen boundary is incomplete"
    assert all(screen.getpixel((column, row)) == border for column in (0, 159) for row in range(144)), "left or right screen boundary is incomplete"


def check_gameplay_background(emulator):
    expected = bytes(value for row in range(8) for value in (0x40 if row == 1 else 0x04 if row == 5 else 0, 0))
    assert bytes(emulator.memory[0x8FF0:0x9000]) == expected, "background pattern overwritten by gameplay effects"
    for row in (*range(15), 30, 31):
        for column in range(19):
            protected = (column < 13 and row < 13) or (column >= 13 and (row == 31 or row < 3 or 6 <= row < 13))
            tile = emulator.memory[0x9800 + row * 32 + column]
            if protected:
                assert tile != 255, "background pattern leaked into grid, score or Next window"
            else:
                assert tile == 255, "outer gameplay background lost its pattern"


def visible_callout(emulator):
    sprites = [
        tuple(emulator.memory[0xFE00 + sprite * 4:0xFE00 + sprite * 4 + 4])
        for sprite in range(3, 3 + CALLOUT_SPRITES)
    ]
    if not all(sprite[0] and CALLOUT_BASE <= sprite[2] < CALLOUT_BASE + CALLOUT_TILES for sprite in sprites):
        return False
    for offset, sprite in enumerate(sprites):
        if sprite[2] != CALLOUT_BASE + offset * 2 or sprite[3] not in (0, 5):
            return False
    actual = bytes(emulator.memory[0x8000 + CALLOUT_BASE * 16:0x8000 + (CALLOUT_BASE + CALLOUT_TILES) * 16])
    return actual in CALLOUT_IMAGES


def check_score_panel(emulator, score=None):
    score_address = SYMBOLS["_game_state"] + 35
    if score is None:
        score = emulator.memory[score_address] | emulator.memory[score_address + 1] << 8
    expected = Image.new("L", (48, 32))
    for row in range(32):
        source_y = row if row < 8 else 20 if row < 24 else row + 16
        for column in range(48):
            offset = (source_y // 8 * 6 + column // 8) * 16 + source_y % 8 * 2
            bit = 7 - column % 8
            expected.putpixel((column, row), (NEXT_FRAME[offset] >> bit & 1) | ((NEXT_FRAME[offset + 1] >> bit & 1) << 1))
    for text, top in (("SCORE", 8), (f"{score:05d}", 18)):
        for index, character in enumerate(text):
            expected.paste(HIGHSCORE_GLYPHS[character].crop((0, 2, 3, 7)), (12 + index * 5, top))
    for row in range(32):
        for column in range(48):
            tile = emulator.memory[0x9800 + ((31 + row // 8) % 32) * 32 + 13 + column // 8]
            assert tile == SCORE_BASE + row // 8 * 6 + column // 8, "score panel map corrupted"
            address = 0x9000 + (tile - 256) * 16 + row % 8 * 2
            bit = 7 - column % 8
            actual = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
            assert actual == expected.getpixel((column, row)), f"score {score} frame or text mismatch at {column},{row}"


def check_score_updates(emulator):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    score_address = SYMBOLS["_game_state"] + 35
    try:
        for score in (0, 1, 10, 999, 12345, 65535, 0):
            emulator.memory[score_address:score_address + 2] = [score & 255, score >> 8]
            press(emulator, "b")
            emulator.tick(30)
            check_score_panel(emulator)
            check_next_pixels(emulator)
            check_screen_boundary(emulator)
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def dice_sheet_pixels(face, variant, styled=True):
    with Image.open(ROOT / "assets/dice/tiled_master.png") as master:
        assert master.size == (96, 48), "legacy dice sheet must retain native pixels"
        source = master.convert("RGBA").crop(((face - 1) * 16, variant * 16, face * 16, (variant + 1) * 16))
    native_sources = {1: "one_18x18.png", 2: "two_18x18.png", 3: "three_18x18.png", 4: "four_18x18.png", 5: "five_18x18.png", 6: "six_18x18.png"}
    if face in native_sources:
        with Image.open(ROOT / "assets/dice" / native_sources[face]) as master:
            assert master.size == (18, 18)
            source = master.convert("RGBA")
    palette = ((229, 240, 183), (139, 172, 15), (48, 98, 48), (13, 56, 0))
    pixels = [0 if color[3] < 128 else min(range(4), key=lambda shade: sum((channel - target) ** 2 for channel, target in zip(color[:3], palette[shade]))) for color in source.getdata()]
    if styled:
        mapping = ((1, 0, 2, 3), (0, 1, 2, 3), (3, 2, 1, 0), (2, 3, 1, 0), (3, 0, 1, 2), (0, 3, 2, 1))[face - 1]
        pixels = [mapping[shade] if color[3] >= 128 else 0 for shade, color in zip(pixels, source.getdata())]
    image = Image.new("L", source.size)
    image.putdata(pixels)
    if face in native_sources:
        if variant == 1:
            image.putdata([3 - shade if color[3] >= 128 else 0 for shade, color in zip(pixels, source.getdata())])
        elif variant == 2:
            draw = ImageDraw.Draw(image)
            draw.line((4, 4, 13, 13), fill=3)
            draw.line((13, 4, 4, 13), fill=3)
    else:
        padded = Image.new("L", (18, 18))
        padded.paste(image, (1, 1))
        image = padded
    return list(image.getdata())


def check_next_pixels(emulator):
    board = SYMBOLS["_game_state"]
    first, second, count = emulator.memory[board + 25:board + 28]
    orientation = emulator.memory[board + 30] & 3
    expected = Image.new("L", (48, 48))
    for row in range(48):
        for column in range(48):
            offset = (row // 8 * 6 + column // 8) * 16 + row % 8 * 2
            bit = 7 - column % 8
            expected.putpixel((column, row), (NEXT_FRAME[offset] >> bit & 1) | ((NEXT_FRAME[offset + 1] >> bit & 1) << 1))
    positions = (((6, 15), (24, 15)), ((15, 6), (15, 24)), ((24, 15), (6, 15)), ((15, 24), (15, 6)))[orientation] if count == 2 else ((15, 15),)
    for face, position in zip((first, second), positions):
        die = Image.new("L", (18, 18))
        die.putdata(dice_sheet_pixels(face, 0))
        expected.paste(die, position)
    for row in range(48):
        for column in range(48):
            tile = emulator.memory[0x9800 + (7 + row // 8) * 32 + 13 + column // 8]
            assert tile == 0 or NEXT_DICE_BASE <= tile < NEXT_DICE_BASE + 32, "Next escaped its reserved tile pool"
            offset = 0x9000 + tile * 16 + row % 8 * 2
            bit = 7 - column % 8
            actual = (emulator.memory[offset] >> bit & 1) | ((emulator.memory[offset + 1] >> bit & 1) << 1)
            assert actual == expected.getpixel((column, row)), f"Next face {first}/{second}, count {count}, rotation {orientation} mismatch at {column},{row}"
    return True


def check_gameplay_hud(emulator):
    for index, character in enumerate(" 0123456789+"):
        expected = Image.new("L", (8, 8))
        expected.paste(HIGHSCORE_GLYPHS[character], (0, 0))
        for row in range(8):
            for column in range(8):
                address = 0x9000 + index * 16 + row * 2
                bit = 7 - column
                actual = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
                assert actual == expected.getpixel((column, row)), "compact score font was overwritten or changed"
    check_score_panel(emulator)
    for index, character in enumerate(" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+!:"):
        atlas_index = ord(character) - 32
        for row in range(8):
            for column in range(8):
                address = 0x8000 + index * 16 + row * 2
                bit = 7 - column
                actual = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
                expected = 3 if SMALL_ATLAS.getpixel((atlas_index % 16 * 8 + column, atlas_index // 16 * 8 + row)) == (224, 248, 207) else 0
                assert actual == expected, "compact background font changed the sprite effect font"


def check_native_board_dice(emulator, output):
    for face in range(1, 7):
        die = dice_sheet_pixels(face, 0)
        assert all(die[row * 18 + column] == 0 for row in range(18) for column in range(18)
                   if column in (0, 17) or row in (0, 17)), "reference dice lost their one-pixel canvas inset"
        assert any(pixel == 3 for pixel in die), f"face {face} lost its reference pips"
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    try:
        emulator.memory[static_address("ui", "reduced_flash")] = 1
        for face in range(1, 7):
            emulator.memory[board:board + 25] = [face] * 25
            emulator.memory[board + 25:board + 30] = [1, 0, 1, 2, 2]
            for direction in ("right", "left"):
                press(emulator, direction)
                emulator.tick(25)
                cursor = emulator.memory[board + 29] * 5 + emulator.memory[board + 28]
                for index in range(25):
                    if index != cursor:
                        assert board_die_pixels(emulator, index) == dice_sheet_pixels(face, 0), f"cell {index}, face {face} differs from the unscaled source"
                emulator.screen.image.save(output)
        for count in (1, 2):
            for face in range(1, 7):
                emulator.memory[board:board + 25] = [0] * 25
                cursor_x = 2 if count == 1 else 4
                emulator.memory[board + 25:board + 31] = [face, 1, count, cursor_x, 2, 3]
                press(emulator, "b")
                emulator.tick(40)
                expected = dice_sheet_pixels(face, 1) if count == 1 else invalid_hatch_pixels()
                assert board_die_pixels(emulator, 10 + cursor_x) == expected, f"face {face}, count {count} has incorrect hover feedback"
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_hover_flash(emulator):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    cache = static_address("ui", "cell_cache")
    enabled = static_address("ui", "hover_enabled")
    frames = static_address("ui", "hover_frames")
    variant_address = static_address("ui", "hover_variant")
    reduced = static_address("ui", "reduced_flash")
    seen = []
    targets = []
    occupied = None
    failures = []

    def capture_frame():
        variant = emulator.memory[variant_address]
        seen.append(variant)
        expected_cache = [6] + [0] * 24
        for index, face in targets:
            if index == occupied:
                expected_cache[index] = 24
                assert board_die_pixels(emulator, index) == invalid_hatch_pixels(), "blocked partner hatch changed during hover flashing"
                continue
            expected_cache[index] = face + variant * 8
            assert board_die_pixels(emulator, index) == dice_sheet_pixels(face, variant), "hover phases differ between pair dice or contain corrupt pixels"
        assert list(emulator.memory[cache:cache + 25]) == expected_cache, "hover flashing changed a settled die or left a trail"

    def capture(_):
        try:
            capture_frame()
        except AssertionError as error:
            failures.append(str(error))

    try:
        cases = [(1, 0, None)] + [(2, orientation, blocked) for orientation in range(4) for blocked in (None, 12, 12 + (1, 5, -1, -5)[orientation])]
        for count, orientation, occupied in cases:
            emulator.memory[board:board + 25] = [6] + [0] * 24
            if occupied is not None:
                emulator.memory[board + occupied] = 3
            emulator.memory[board + 25:board + 31] = [1, 5, count, 2, 2, (orientation - 1) % 4]
            emulator.memory[reduced] = 0
            emulator.memory[enabled] = 0
            press(emulator, "b")
            emulator.tick(25)
            targets = [(12, 1)] + ([(12 + (1, 5, -1, -5)[orientation], 5)] if count == 2 else [])
            before = bytes(emulator.memory[board:board + 37])
            seen.clear()
            emulator.hook_register(0, SYMBOLS["_ui_tick"], capture, None)
            try:
                clock = []
                for _ in range(64):
                    emulator.tick()
                    clock.append(emulator.memory[frames])
                assert not failures, failures[:3]
                assert set(clock) == set(range(16)), "hover clock is not a 16-VBlank cycle"
                assert all(3 <= clock.count(value) <= 5 for value in range(16)), "hover clock depends on rendering speed instead of VBlank"
                assert set(seen) == {0, 1}, "hover clock does not alternate normal/inverted"
                assert sum(first != second for first, second in zip(seen, seen[1:])) >= 6, "hover animation lost phase changes"
            finally:
                emulator.hook_deregister(0, SYMBOLS["_ui_tick"])
            assert bytes(emulator.memory[board:board + 37]) == before, "hover animation changed game mechanics"
            check_next_pixels(emulator)
            check_screen_boundary(emulator)
        emulator.memory[reduced] = 1
        emulator.tick(25)
        assert emulator.memory[reduced] == 1
        seen.clear()
        emulator.hook_register(0, SYMBOLS["_ui_tick"], capture, None)
        try:
            emulator.tick(64)
            assert not failures, failures[:3]
            assert seen and set(seen) == {1}, "reduced-flashing mode still blinks hovering dice"
        finally:
            emulator.hook_deregister(0, SYMBOLS["_ui_tick"])
        press(emulator, "start")
        wait_screen(emulator, 5)
        assert not emulator.memory[enabled], "hover animation leaked into the pause menu"
        paused_frame = emulator.memory[frames]
        emulator.tick(32)
        assert emulator.memory[frames] == paused_frame
        press(emulator, "b")
        wait_screen(emulator, 4)
        assert emulator.memory[enabled], "hover did not restart after pause"
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_native_preview_dice(emulator, output):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    try:
        for count in (2, 1):
            for face in range(1, 7):
                for second in (range(1, 7) if count == 2 else (0,)):
                    emulator.memory[board:board + 25] = [face, second] + [0] * 23
                    emulator.memory[board + 25:board + 31] = [face, second, count, 2, 2, 3]
                    for orientation in range(4 if count == 2 else 1):
                        press(emulator, "b")
                        emulator.tick(40)
                        if count == 2:
                            assert emulator.memory[board + 30] == orientation, "B did not rotate the pair"
                        check_screen_boundary(emulator)
                        check_next_pixels(emulator)
                        if face == 1 and second in (0, 1, 2):
                            emulator.screen.image.save(output.with_name(f"{output.stem}-{count}-dice-{second}-{orientation}.png"))
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def static_address(module, variable):
    return next(address for name, address in SYMBOLS.items() if name.startswith(f"F{module}${variable}$"))


def board_die_pixels(emulator, index):
    pixels = []
    for row in range(18):
        for column in range(18):
            pixel_x = index % 5 * 20 + 1 + column
            pixel_y = index // 5 * 20 + 1 + row
            tile = BOARD_BASE + pixel_y // 8 * BOARD_TILE_WIDTH + pixel_x // 8
            address = 0x9000 + (tile if tile < 128 else tile - 256) * 16 + pixel_y % 8 * 2
            bit = 7 - pixel_x % 8
            pixels.append((emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1))
    return pixels


def invalid_hatch_pixels():
    return [3 if 2 <= column < 16 and 2 <= row < 16 and (column + row - 2) % 6 < 2 else 0 for row in range(18) for column in range(18)]


def check_invalid_preview(emulator, output):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    unchanged_art = static_gameplay_art(emulator)
    cases = (
        ("occupied-origin", 1, 2, 2, 0, 12, "left"),
        ("occupied-origin-pair", 2, 2, 2, 0, 12, "left"),
        ("occupied-neighbor", 2, 2, 2, 0, 13, "left"),
        ("occupied-above", 2, 2, 2, 3, 7, "left"),
        ("right-edge", 2, 4, 2, 0, None, "left"),
        ("bottom-edge", 2, 2, 4, 1, None, "up"),
        ("left-edge", 2, 0, 2, 2, None, "right"),
        ("top-edge", 2, 2, 0, 3, None, "down"),
    )
    try:
        emulator.memory[SYMBOLS["_audio_enabled"]] = 1
        emulator.memory[static_address("ui", "reduced_flash")] = 1
        for name, count, cursor_x, cursor_y, orientation, occupied, direction in cases:
            emulator.memory[board:board + 25] = [0] * 25
            if occupied is not None:
                emulator.memory[board + occupied] = 3
            emulator.memory[board + 25:board + 31] = [1, 2, count, cursor_x, cursor_y, (orientation - 1) % 4 if count == 2 else 0]
            press(emulator, "b")
            emulator.tick(40)
            assert check_next_pixels(emulator), f"hover/rotation triggered the invalid mascot for {name}"
            origin = cursor_y * 5 + cursor_x
            cache = static_address("ui", "cell_cache")
            if occupied is not None:
                assert board_die_pixels(emulator, occupied) == invalid_hatch_pixels(), "occupied target did not show the diagonal hatch"
                assert emulator.memory[cache + occupied] == 24
                if count == 2:
                    empty = origin if occupied != origin else origin + (1, 5, -1, -5)[orientation]
                    face = 1 if occupied != origin else 2
                    assert emulator.memory[cache + empty] == face + 8, "empty partner lost its reduced-flashing hover highlight"
                    assert board_die_pixels(emulator, empty) == dice_sheet_pixels(face, 1), "empty partner is not the native inverted die"
            else:
                assert emulator.memory[cache + origin] == 24, "off-grid pair did not use the invalid hatch"
                assert board_die_pixels(emulator, origin) == invalid_hatch_pixels(), "off-grid marker differs from occupied-cell marker"
            before = bytes(emulator.memory[board:board + 37])
            emulator.button_press("a")
            sound_frames = 0
            overlay_seen = False
            for frame in range(45):
                emulator.tick()
                audible = bool(emulator.memory[0xFF26] & 0x08)
                sound_frames += audible
                actual_map = [emulator.memory[0x9800 + row * 32 + column] for row in range(7, 13) for column in range(13, 19)]
                if audible and actual_map == INVALID_MAP and bytes(emulator.memory[NEXT_VRAM:NEXT_VRAM + len(INVALID_BYTES)]) == INVALID_BYTES:
                    overlay_seen = True
                    emulator.screen.image.save(output.with_name(f"{output.stem}-{name}.png"))
                if frame >= 23:
                    assert not audible, "invalid sound continued or retriggered while A was held"
                    assert check_next_pixels(emulator), "mascot outlasted the invalid sound"
            emulator.button_release("a")
            emulator.tick(3)
            assert 18 <= sound_frames <= 20, f"invalid sound lasted {sound_frames} frames instead of 19"
            assert overlay_seen, f"rejected A press did not show the falling mascot during the sound for {name}"
            assert bytes(emulator.memory[board:board + 37]) == before, "invalid placement changed the board or score"
            assert static_gameplay_art(emulator) == unchanged_art, "invalid overlay overwrote other static art"
            check_screen_boundary(emulator)
            emulator.screen.image.save(output.with_name(f"{output.stem}-{name}-expired.png"))
            if name == "right-edge":
                press(emulator, "b")
                emulator.tick(40)
                assert check_next_pixels(emulator), "rotation to a valid orientation did not restore preview dice"
                for _ in range(3):
                    press(emulator, "b")
                    emulator.tick(40)
            press(emulator, direction)
            emulator.tick(40)
            assert check_next_pixels(emulator), f"valid move after {name} did not restore all six native dice"
            assert static_gameplay_art(emulator) == unchanged_art
            emulator.screen.image.save(output.with_name(f"{output.stem}-{name}-restored.png"))
        emulator.memory[board + 25:board + 31] = [1, 2, 2, 4, 2, 3]
        press(emulator, "b")
        emulator.tick(30)
        press(emulator, "a")
        press(emulator, "a")
        assert emulator.memory[0xFF26] & 0x08, "a fresh rejected A press did not restart the sound"
        press(emulator, "start")
        wait_screen(emulator, 5)
        assert not emulator.memory[0xFF26] & 0x08, "invalid sound leaked into the pause screen"
        press(emulator, "b")
        wait_screen(emulator, 4)
        assert check_next_pixels(emulator), "invalid mascot reappeared after pause"
        emulator.memory[SYMBOLS["_audio_enabled"]] = 0
        press(emulator, "a")
        emulator.tick(30)
        assert not emulator.memory[0xFF26] & 0x08, "muted invalid move played a sound"
        assert check_next_pixels(emulator), "muted invalid move displayed the sound-linked mascot"
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_flying_scores(emulator, cgb, output):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    cache = static_address("ui", "score_cache")
    popup_base = int(re.search(r"#define ART_SCORE_POPUP_BASE (\d+)u", ART_HEADER).group(1))
    trace = []
    failures = []
    expected_pixels = []
    neighbors = {0: (1, 5), 4: (3, 9), 12: (11, 13), 20: (15, 21), 24: (19, 23)}

    def capture_frame():
        sprites = list(emulator.memory[SYMBOLS["_shadow_OAM"]:SYMBOLS["_shadow_OAM"] + 12])
        if not sprites[0] or sprites[2] != popup_base:
            return
        displayed = emulator.memory[cache] | emulator.memory[cache + 1] << 8
        trace.append((sprites[1] - 8, sprites[0] - 16, displayed))
        check_score_panel(emulator, displayed)
        check_next_pixels(emulator)
        assert not emulator.memory[static_address("ui", "hover_enabled")], "hover resumed during score flight"
        width = len(str(award)) * 8
        for sprite in range(3):
            offset = sprite * 4
            if sprite * 8 < width:
                assert sprites[offset:offset + 4] == [sprites[0], sprites[1] + sprite * 8, popup_base + sprite, 2 if cgb else 16], "score sprite pieces lost alignment or contrast palette"
            else:
                assert sprites[offset:offset + 2] == [0, 0], "unused score sprite is visible"
        actual = []
        for row in range(8):
            for column in range(24):
                address = 0x8000 + (popup_base + column // 8) * 16 + row * 2
                bit = 7 - column % 8
                actual.append((emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1))
        assert actual == expected_pixels, "flying score lost its bold title font"
        if len(trace) == 10:
            emulator.screen.image.save(output.with_name(f"{output.stem}-{origin}-{reduced}.png"))

    def capture(_):
        try:
            capture_frame()
        except AssertionError as error:
            failures.append(str(error))

    try:
        for face, origin, reduced, initial_score in ((1, 0, 0, 0), (4, 12, 0, 999), (6, 24, 0, 65500), (1, 4, 0, 65534), (6, 20, 1, 90), (1, 12, 1, 9999)):
            snapshot.seek(0)
            emulator.load_state(snapshot)
            emulator.memory[board:board + 25] = [0] * 25
            for neighbor in neighbors[origin]:
                emulator.memory[board + neighbor] = face
            emulator.memory[board + 25:board + 37] = [face, 0, 1, origin % 5, origin // 5, 0, 0, 0, 0, 0, initial_score & 255, initial_score >> 8]
            emulator.memory[static_address("ui", "reduced_flash")] = reduced
            press(emulator, "b")
            emulator.tick(30)
            check_score_panel(emulator)
            award = face * 3 + (25 if face == 4 else 100 if face == 6 else 0)
            expected_pixels = []
            for row in range(8):
                for column in range(24):
                    digit_index = column // 8
                    if digit_index >= len(str(award)):
                        expected_pixels.append(0)
                        continue
                    offset = (ord(str(award)[digit_index]) - ord("0")) * 16 + row * 2
                    bit = 7 - column % 8
                    expected_pixels.append((SCORE_POPUP_DIGITS[offset] >> bit & 1) | ((SCORE_POPUP_DIGITS[offset + 1] >> bit & 1) << 1))
            trace.clear()
            failures.clear()
            emulator.hook_register(0, SYMBOLS["_service_animation_input"], capture, None)
            try:
                press(emulator, "a")
                for _ in range(300):
                    emulator.tick()
                assert not failures, failures[:3]
            finally:
                emulator.hook_deregister(0, SYMBOLS["_service_animation_input"])
            width = len(str(award)) * 8
            start_x = 15 + origin % 5 * 20 - width // 2
            start_y = 13 + origin // 5 * 20
            target_x = 133 - width // 2
            expected = [(start_x, start_y, initial_score)] * (16 if reduced else 1)
            position_x, position_y = start_x, start_y
            if not reduced:
                while (position_x, position_y) != (target_x, 31):
                    position_x += min(6, target_x - position_x)
                    position_y += min(6, 31 - position_y) if position_y < 31 else -min(6, position_y - 31)
                    expected.append((position_x, position_y, initial_score))
            expected.extend([(position_x, position_y, (initial_score + award) & 65535)] * 2)
            assert trace == expected, f"score flight at {origin} lost its C64 timing, route or deferred total update"
            check_gameplay_hud(emulator)
            assert not any(emulator.memory[SYMBOLS["_shadow_OAM"] + sprite * 4] for sprite in range(3)), "score popup left visible sprites after landing"
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_atari_effects(emulator):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    cache = static_address("ui", "cell_cache")
    reduced_flash = static_address("ui", "reduced_flash")
    star_tile = int(re.search(r"#define ART_STAR_TILE (\d+)u", ART_HEADER).group(1))
    trace = []
    shake_frames = 0
    shake_map = None
    failures = []

    def capture_frame():
        nonlocal shake_map
        emulator.memory[0x0000] = 0x0A
        canonical = bytes(emulator.memory[0xA300:0xA300 + BOARD_TILES * 16])
        emulator.memory[0x0000] = 0x00
        actual = bytes(emulator.memory[0x9000 + (tile if tile < 128 else tile - 256) * 16 + byte] for tile in range(BOARD_BASE, BOARD_BASE + BOARD_TILES) for byte in range(16))
        if len(trace) < shake_frames:
            shifted = (len(trace) & 1) == 0
            expected = bytearray(canonical)
            if shifted:
                for tile_row in range(BOARD_TILE_WIDTH):
                    for byte in range(16):
                        addresses = [(tile_row * BOARD_TILE_WIDTH + column) * 16 + byte for column in range(BOARD_TILE_WIDTH)]
                        row = int.from_bytes(bytes(canonical[address] for address in addresses), "big") >> 2
                        for address, value in zip(addresses, row.to_bytes(BOARD_TILE_WIDTH, "big")):
                            expected[address] = value
            assert actual == expected, "grid shake does not translate the complete board by exactly two pixels"
            tilemap = bytes(emulator.memory[0x9800:0x9C00])
            if shake_map is None:
                shake_map = tilemap
            assert tilemap == shake_map, "grid shake changed the board map, score, Next window or screen boundary"
            assert (emulator.memory[0xFF43], emulator.memory[0xFF42]) == (251, 234), "grid shake moved the whole screen"
        callout = visible_callout(emulator)
        if callout:
            assert actual == canonical, "grid callout modified the board tiles"
            check_score_panel(emulator)
            check_next_pixels(emulator)
            check_gameplay_background(emulator)
        if any(emulator.memory[SYMBOLS["_shadow_OAM"] + sprite * 4 + 2] == star_tile for sprite in range(8)):
            star_data = emulator.memory[0x8000 + star_tile * 16:0x8000 + (star_tile + 1) * 16]
            assert sum((star_data[row * 2] >> bit & 1) or (star_data[row * 2 + 1] >> bit & 1) for row in range(8) for bit in range(8)) == 1, "merge firework is not a single-pixel particle"
            assert star_data[8] == star_data[9] == 0x08, "merge firework is not using the darkest sprite shade"
            companion = emulator.memory[0x8000 + (star_tile + 1) * 16:0x8000 + (star_tile + 2) * 16]
            assert bytes(companion) == bytes(16), "merge particle can expose score-popup tiles in 8x16 mode"
        trace.append((tuple(emulator.memory[cache:cache + 25]), actual != canonical, bytes(emulator.memory[SYMBOLS["_shadow_OAM"]:SYMBOLS["_shadow_OAM"] + 32]), emulator.memory[0xFF47], emulator.memory[static_address("ui", "hover_enabled")]))

    def capture(_):
        try:
            capture_frame()
        except AssertionError as error:
            failures.append(str(error))

    def prepare(face, origin, reduced):
        nonlocal shake_frames, shake_map
        snapshot.seek(0)
        emulator.load_state(snapshot)
        emulator.memory[board:board + 25] = [0] * 25
        neighbors = {0: (1, 5), 12: (11, 13), 24: (19, 23)}[origin]
        for index in neighbors:
            emulator.memory[board + index] = face
        emulator.memory[board + 25:board + 37] = [face, 0, 1, origin % 5, origin // 5, 0, 0, 0, 0, 0, 0, 0]
        emulator.memory[reduced_flash] = reduced
        press(emulator, "b")
        emulator.tick(40)
        trace.clear()
        failures.clear()
        shake_frames = (4 if face == 6 else 2) if face >= 5 and not reduced else 0
        shake_map = None

    emulator.hook_register(0, SYMBOLS["_service_animation_input"], capture, None)
    try:
        for face, origin, reduced in ((1, 12, 0), (4, 12, 0), (5, 0, 0), (6, 24, 0), (5, 12, 1), (6, 12, 1)):
            prepare(face, origin, reduced)
            press(emulator, "a")
            emulator.tick(300)
            assert not failures, failures[:3]
            check_gameplay_hud(emulator)
            assert emulator.memory[board + origin] == (face + 1 if face < 6 else 0)
            assert trace, "merge did not poll animation input"
            assert all(not entry[4] for entry in trace[:-1]), "hover animation continued during a merge effect"
            if reduced:
                assert len(trace) == 73, "reduced flashing did not retain the particle-burst delay"
                assert all(entry[1] == 0 for entry in trace), "reduced flashing still shakes the board"
                assert any(any(entry[2][sprite * 4] and entry[2][sprite * 4 + 2] == star_tile for sprite in range(8)) for entry in trace), "merge particle explosion did not run"
                assert len({entry[3] for entry in trace}) == 1, "reduced flashing still changes the DMG palette"
            else:
                if face >= 5:
                    expected_bump = [True, False] * (2 if face == 6 else 1)
                    assert [entry[1] for entry in trace[:shake_frames]] == expected_bump, "five/six board bump did not use the expected duration"
                else:
                    assert not any(entry[1] for entry in trace), "faces below five should not shake"
                start = shake_frames + (5 if face == 6 else 0)
                origin_x, origin_y = origin % 5, origin // 5
                for step in range(5):
                    left, right = min(step, origin_x), max(4 - step, origin_x)
                    top, bottom = min(step, origin_y), max(4 - step, origin_y)
                    points = {(left, origin_y), (right, origin_y), (origin_x, top), (origin_x, bottom)}
                    if face >= 5:
                        points.update(((left, top), (right, top), (left, bottom), (right, bottom)))
                    expected = {row * 5 + column for column, row in points}
                    for entry in trace[start + step * 2:start + step * 2 + 2]:
                        assert {index for index, value in enumerate(entry[0]) if 8 <= value < 15} == expected, f"face {face} ripple step {step} does not converge from the board edges"
                start += 10
                velocity_x = (-3, -2, 0, 2, 3, -3, 0, 3)
                velocity_y = (-3, -4, -5, -4, -3, 2, 4, 2)
                assert len(trace) >= start + 24, "particle explosion ended before twelve steps"
                for step in range(12):
                    for entry in trace[start + step * 2:start + step * 2 + 2]:
                        for sprite in range(8):
                            actual_y, actual_x, tile, _ = entry[2][sprite * 4:sprite * 4 + 4]
                            expected_x = min(152, max(0, 11 + origin_x * 20 + velocity_x[sprite] * step)) + 8
                            expected_y = min(136, max(0, 28 + origin_y * 20 + velocity_y[sprite] * step + step * step // 3)) + 16
                            assert (actual_x, actual_y, tile) == (expected_x, expected_y, star_tile), f"particle {sprite}, step {step} lost its explosion trajectory or wrapped at a screen edge"
            check_screen_boundary(emulator)

        for latest in ("left", "b"):
            prepare(1, 12, 0)
            emulator.button_press("a")
            emulator.tick(2)
            emulator.button_release("a")
            for _ in range(160):
                if len(trace) >= 30:
                    break
                emulator.tick()
            assert 30 <= len(trace) < 40, "missed the score-award input-buffer test window"
            for button in ("right", latest):
                emulator.button_press(button)
                emulator.tick(2)
                emulator.button_release(button)
                emulator.tick(2)
            assert emulator.memory[static_address("main", "queued_action")] == (2 if latest == "left" else 32), "latest brief movement/rotation was lost during a merge"
            emulator.button_press("a")
            emulator.tick(220)
            emulator.button_release("a")
            emulator.tick(5)
            assert sum(bool(value) for value in emulator.memory[board:board + 25]) == 1, "A pressed during effects placed the next piece"
            assert emulator.memory[board + 28] == (1 if latest == "left" else 2), "queued action was lost, replayed more than once, or applied before spawning"
            if latest == "b":
                assert emulator.memory[board + 30] == (1 if emulator.memory[board + 27] == 2 else 0), "queued rotation did not apply to the newly spawned piece"
            assert emulator.memory[static_address("main", "queued_action")] == 0
    finally:
        emulator.hook_deregister(0, SYMBOLS["_service_animation_input"])
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_result_numbers(emulator, score, best):
    for value, top in ((score, 52), (best, 64)):
        for index, digit in enumerate(f"{value:05d}"):
            for row in range(8):
                actual = 0
                for column in range(6):
                    pixel_x = 107 + index * 7 + column
                    pixel_y = top + row
                    tile = emulator.memory[0x9800 + pixel_y // 8 * 32 + pixel_x // 8]
                    address = 0x9000 + (tile if tile < 128 else tile - 256) * 16 + pixel_y % 8 * 2
                    bit = 7 - pixel_x % 8
                    shade = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
                    assert shade in (0, 3), "result digit has an unexpected shade"
                    actual = (actual << 1) | (shade == 3)
                expected = sum(1 << (5 - column) for column in range(LANKY_GLYPHS[digit].width) if LANKY_GLYPHS[digit].getpixel((column, row)))
                assert actual == expected, f"result {value:05d} rendered the wrong digit at position {index}"


def check_instruction_page(emulator, page):
    assert INSTRUCTION_PAGES == 1 and page == 0, "legacy instruction pages remain"
    actual_map = [emulator.memory[0x9800 + row * 32 + column] for row in range(18) for column in range(20)]
    assert actual_map == INSTRUCTION_MAPS, "instructions have stale or missing tiles"
    assert emulator.memory[0xFF40] & 0x80, "instructions disabled the display"
    assert not emulator.memory[0xFF40] & 2, "sprites from the previous screen leaked onto instructions"
    assert not emulator.memory[0xFF40] & 0x10, "instructions lost signed tile addressing"
    assert emulator.memory[0xFF42] == emulator.memory[0xFF43] == 0, "gameplay scroll displaced instructions"
    with Image.open(ROOT / "assets/instructions_master.png") as master:
        assert master.size == (160, 144)
        source = master.convert("RGB")
        reference = source.quantize(colors=4, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    colors = [tuple(reference.getpalette()[index * 3:index * 3 + 3]) for index in range(4)]
    order = sorted(range(4), key=lambda index: colors[index][0] * 299 + colors[index][1] * 587 + colors[index][2] * 114, reverse=True)
    palette = [colors[index] for index in order]
    expected_image = Image.new("L", (160, 144))
    expected_image.putdata([min(range(4), key=lambda shade: sum((channel - target) ** 2 for channel, target in zip(color, palette[shade]))) for color in source.getdata()])
    draw = ImageDraw.Draw(expected_image)
    draw.rectangle((85, 57, 145, 100), fill=0)
    text_positions = [(text, 87, 58 + index * 8) for index, text in enumerate(("1. PLACE DICE", "2. MATCH 3+", "3. MERGE UP", "4. MAKE CHAINS", "5. REACH SIX!"))]
    draw.rectangle((21, 128, 140, 138), fill=0)
    for text, left, top in text_positions:
        for character in text:
            glyph = HIGHSCORE_GLYPHS[character]
            expected_image.paste(glyph, (left, top))
            left += glyph.width + 1
    for row in range(144):
        for column in range(160):
            tile = actual_map[row // 8 * 20 + column // 8]
            address = 0x9000 + (tile if tile < 128 else tile - 256) * 16 + row % 8 * 2
            bit = 7 - column % 8
            actual = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
            assert actual == expected_image.getpixel((column, row)), f"instructions lost native Itty Bitty lettering or changed the surrounding artwork at {column},{row}"


def check_highscore_panel(emulator, page):
    scores = SYMBOLS["_score_table"]
    for entry in range(5):
        index = page * 5 + entry
        value = emulator.memory[scores + index * 5 + 3] | emulator.memory[scores + index * 5 + 4] << 8
        floating = index == 0 and emulator.memory[SYMBOLS["_screen_state"]] == 1
        initials = bytes(emulator.memory[scores + index * 5:scores + index * 5 + 3]).decode("ascii")
        initials_width = sum(HIGHSCORE_GLYPHS[character].width + 1 for character in initials) - 1
        rank_left = 80 + (72 - initials_width - 35) // 2 if floating else 84 if index == 9 else 88
        score_left = rank_left + 4 + initials_width + 1 if floating else 118
        for text, left, advance in ((f"{value:05d}", score_left, 6), (str(index + 1), rank_left, 4)):
            for position, digit in enumerate(text):
                for row in range(8):
                    actual = 0
                    for column in range(HIGHSCORE_GLYPHS[digit].width):
                        pixel_x = left + position * advance + column
                        pixel_y = 60 + entry * 11 + row
                        if floating:
                            local_x = pixel_x - 80
                            tile = emulator.memory[0xFE02 + (local_x // 8) * 4]
                            address = 0x8000 + tile * 16 + row * 2
                            bit = 7 - local_x % 8
                        else:
                            tile = emulator.memory[0x9800 + pixel_y // 8 * 32 + pixel_x // 8]
                            address = 0x9000 + (tile if tile < 128 else tile - 256) * 16 + pixel_y % 8 * 2
                            bit = 7 - pixel_x % 8
                        shade = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
                        actual = (actual << 1) | (shade == 3)
                    expected = sum(1 << (HIGHSCORE_GLYPHS[digit].width - 1 - column) for column in range(HIGHSCORE_GLYPHS[digit].width) if HIGHSCORE_GLYPHS[digit].getpixel((column, row)))
                    assert actual == expected, f"high-score rank {index + 1}, value {value}: incorrect digit {position}"


def check_highscore_animation(emulator):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    try:
        delay_symbol = re.search(r"00:([0-9A-Fa-f]+) Fpresentation\$highscore_delay\$", (ROOT / "build/sixies.sym").read_text())
        remaining = emulator.memory[int(delay_symbol.group(1), 16)]
        assert 45 <= remaining <= 60, "top row did not start with a one-second delay"
        background = bytes(emulator.memory[0x8800:0x9C00])
        footer = emulator.screen.image.crop((0, 128, 160, 144))
        assert len(footer.getcolors()) == 1, "high-score browsing footer still contains text"
        for _ in range(remaining - 1):
            assert emulator.memory[0xFE01] == 88, "top score moved before one second"
            emulator.tick()
        emulator.tick(3)
        assert emulator.memory[0xFE01] == 89, "top score did not start moving after one second"
        positions = []
        for _ in range(100):
            emulator.tick()
            position = emulator.memory[0xFE01]
            positions.append(position)
            assert 85 <= position <= 91, "highest-score row escaped its panel"
            for sprite in range(9):
                assert emulator.memory[0xFE00 + sprite * 4] == 76, "top row moved vertically"
                assert emulator.memory[0xFE01 + sprite * 4] == position + sprite * 8, "top row sprite spacing changed"
            assert bytes(emulator.memory[0x8800:0x9C00]) == background, "animation changed other rows or screen artwork"
        assert min(positions) == 85 and max(positions) == 91, "top row did not move both left and right"
        check_highscore_panel(emulator, 0)
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_wide_initials(emulator, rank):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    try:
        address = SYMBOLS["_score_table"] + rank * 5
        emulator.memory[address:address + 3] = b"MWM"
        press(emulator, "left")
        left = 0
        for position, character in enumerate("MWM"):
            glyph = HIGHSCORE_GLYPHS[character]
            for row in range(8):
                for column in range(glyph.width):
                    pixel_x = left + column
                    tile = emulator.memory[0xFE02 + pixel_x // 8 * 4]
                    tile_address = 0x8000 + tile * 16 + row * 2
                    bit = 7 - pixel_x % 8
                    shade = (emulator.memory[tile_address] >> bit & 1) | ((emulator.memory[tile_address + 1] >> bit & 1) << 1)
                    ink = bool(glyph.getpixel((column, row)))
                    expected = (1 if ink else 3) if position == 2 else (3 if ink else 0)
                    assert shade == expected, f"wide initial {character} was clipped or corrupted"
            left += glyph.width + 1
        check_highscore_panel(emulator, rank // 5)
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_game_over_flow(emulator):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    scores = SYMBOLS["_score_table"]
    best = emulator.memory[scores + 3] | emulator.memory[scores + 4] << 8
    try:
        frames = 0
        while emulator.memory[SYMBOLS["_screen_state"]] == 6 and frames < 95:
            emulator.tick()
            frames += 1
        assert 60 <= frames <= 90, f"game-over timeout took {frames} remaining frames"
        wait_screen(emulator, 10)
        emulator.tick(120)
        assert emulator.memory[SYMBOLS["_screen_state"]] == 10, "results screen did not wait for a choice"
        for button in ("a", "b"):
            snapshot.seek(0)
            emulator.load_state(snapshot)
            emulator.button_press(button)
            emulator.tick(5)
            assert emulator.memory[SYMBOLS["_screen_state"]] == 10, f"{button.upper()} did not skip Game Over immediately"
            emulator.tick(115)
            assert emulator.memory[SYMBOLS["_screen_state"]] == 10, "held splash-skip button also selected a results option"
            emulator.button_release(button)
            emulator.tick(5)
        for score in (0, 400, 44444, 65535):
            snapshot.seek(0)
            emulator.load_state(snapshot)
            emulator.memory[board + 35:board + 37] = [score & 255, score >> 8]
            press(emulator, "b")
            wait_screen(emulator, 10)
            check_result_numbers(emulator, score, max(best, score))
            assert emulator.memory[0xFE00] == 100, "Try Again was not selected by default"
            press(emulator, "down")
            assert emulator.memory[0xFE00] == 114, "cursor did not move to Main Menu"
            press(emulator, "up")
            assert emulator.memory[0xFE00] == 100, "cursor did not return to Try Again"
            if score == 0:
                menu = BytesIO()
                emulator.save_state(menu)
                press(emulator, "a")
                wait_screen(emulator, 4)
                assert emulator.memory[board + 35:board + 37] == [0, 0], "Try Again did not reset the score"
                menu.seek(0)
                emulator.load_state(menu)
                press(emulator, "down")
                press(emulator, "a")
                wait_screen(emulator, 11)
                menu.seek(0)
                emulator.load_state(menu)
                press(emulator, "b")
                wait_screen(emulator, 11)
            else:
                press(emulator, "down")
                press(emulator, "a")
                wait_screen(emulator, 7)
                rank = 8 if score == 400 else 0
                check_highscore_panel(emulator, rank // 5)
                check_wide_initials(emulator, rank)
                press(emulator, "down")
                assert emulator.memory[scores + rank * 5] == ord("Z"), "initial did not wrap A to Z"
                press(emulator, "up")
                assert emulator.memory[scores + rank * 5] == ord("A"), "initial did not wrap Z to A"
                press(emulator, "right")
                press(emulator, "up")
                press(emulator, "b")
                press(emulator, "up")
                press(emulator, "a")
                press(emulator, "a")
                press(emulator, "up")
                check_highscore_panel(emulator, rank // 5)
                press(emulator, "a")
                wait_screen(emulator, 11)
                assert bytes(emulator.memory[scores + rank * 5:scores + rank * 5 + 3]) == b"BBB", "A-confirmed initials were not retained"
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def start_menu_reference(selection):
    palette = ((213, 231, 160), (149, 186, 104), (83, 126, 67), (22, 61, 29))
    with Image.open(ROOT / "assets/start_menu_master.png") as master:
        source = master.convert("RGB")
    reference = Image.new("L", source.size)
    reference.putdata([min(range(4), key=lambda shade: sum((pixel[channel] - palette[shade][channel]) ** 2 for channel in range(3))) for pixel in source.getdata()])
    draw = ImageDraw.Draw(reference)
    draw.rectangle((91, 63, 152, 79), fill=0)
    draw.rectangle((82, 64, 89, 79), fill=0)
    draw.rectangle((96, 64, 150, 118), fill=0)
    draw.rectangle((16, 128, 144, 136), fill=0)
    for text, left, text_top in (("Play", 96, 67), ("Settings", 96, 81), ("How to Play", 96, 94), ("High Scores", 96, 107), ("Roll + Place + Chain!", 20, 128)):
        for character in text:
            glyph = LANKY_GLYPHS[character]
            reference.paste(glyph, (left, text_top), glyph.point(lambda shade: 255 if shade else 0))
            left += glyph.width + 1
    top = (64, 79, 92, 105)[selection]
    label = reference.crop((96, top + 2, 150, top + 12))
    draw.rounded_rectangle((92, top, 151, top + 14), radius=3, fill=1, outline=3)
    reference.paste(label, (96, top + 2), label.point(lambda shade: 255 if shade >= 2 else 0))
    return reference


START_MENU_REFERENCES = tuple(start_menu_reference(selection) for selection in range(4))


def check_start_menu_selection(emulator, selection):
    expected = START_MENU_MAP.copy()
    top = (8, 9, 11, 13)[selection]
    for row in range(3):
        for column in range(8):
            expected[(top + row) * 20 + 11 + column] = 224 + row * 8 + column
    actual = [emulator.memory[0x9800 + row * 32 + column] for row in range(18) for column in range(20)]
    assert actual == expected, "start-menu highlight left stale tiles or damaged the artwork"
    assert emulator.memory[0xFE00] == (80, 95, 108, 121)[selection], "start-menu arrow is on the wrong option"
    reference = START_MENU_REFERENCES[selection]
    for top, bottom, left, right in ((64, 120, 96, 152), (128, 136, 16, 144)):
        for pixel_y in range(top, bottom):
            for pixel_x in range(left, right):
                tile = actual[pixel_y // 8 * 20 + pixel_x // 8]
                address = 0x9000 + (tile if tile < 128 else tile - 256) * 16 + pixel_y % 8 * 2
                bit = 7 - pixel_x % 8
                shade = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
                assert shade == reference.getpixel((pixel_x, pixel_y)), f"start-menu text corrupted at ({pixel_x}, {pixel_y}) with option {selection} selected"


def check_pause_screen(emulator, selection):
    scores = SYMBOLS["_score_table"]
    sound = emulator.memory[scores + 50]
    reduced = emulator.memory[scores + 51]
    with Image.open(ROOT / "assets/pause_master.png") as master:
        source = master.convert("RGB").resize((160, 144), Image.Resampling.LANCZOS)
    indexed = source.quantize(colors=4, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    palette = [tuple(indexed.getpalette()[index * 3:index * 3 + 3]) for index in range(4)]
    palette.sort(key=lambda color: color[0] * 299 + color[1] * 587 + color[2] * 114, reverse=True)
    expected = Image.new("L", (160, 144))
    expected.putdata([min(range(4), key=lambda shade: sum((channel - target) ** 2 for channel, target in zip(color, palette[shade]))) for color in source.getdata()])
    text_regions = [(8, top, 101, bottom) for top, bottom in ((41, 52), (55, 66), (69, 80), (83, 96), (97, 111))] + [(9, 130, 145, 139)]
    for left, top, right, bottom in text_regions:
        span = bottom - top + 1
        for column in range(left, right):
            upper = source.getpixel((column, top - 1))
            lower = source.getpixel((column, bottom))
            for row in range(top, bottom):
                progress = row - top + 1
                color = tuple((above * (span - progress) + below * progress + span // 2) // span for above, below in zip(upper, lower))
                expected.putpixel((column, row), min(range(4), key=lambda shade: sum((channel - target) ** 2 for channel, target in zip(color, palette[shade]))))
    labels = ("RESUME", "INSTRUCTIONS", "SOUND ON" if sound else "SOUND OFF", "FLASH REDUCED" if reduced else "FLASH FULL", "NEW GAME")
    text_positions = [(text, 24, 42 + row * 14) for row, text in enumerate(labels)]
    text_positions.append(("+", 10, 42 + selection * 14))
    footer = "A CHOOSE   B RESUME"
    footer_width = sum(HIGHSCORE_GLYPHS[character].width + 1 for character in footer) - 1
    text_positions.append((footer, (160 - footer_width) // 2, 130))
    for text, left, top in text_positions:
        for character in text:
            glyph = HIGHSCORE_GLYPHS[character]
            for glyph_row in range(8):
                for glyph_column in range(glyph.width):
                    if glyph.getpixel((glyph_column, glyph_row)):
                        expected.putpixel((left + glyph_column, top + glyph_row), 3)
            left += glyph.width + 1
    assert emulator.memory[SYMBOLS["_screen_state"]] == 5
    assert emulator.memory[0xFF40] & 0x80 and not emulator.memory[0xFF40] & 0x12, "pause screen has the wrong tile mode or leftover sprites"
    assert emulator.memory[0xFF42] == emulator.memory[0xFF43] == 0, "pause screen inherited gameplay scrolling"
    for row in range(144):
        for column in range(160):
            tile = emulator.memory[0x9800 + row // 8 * 32 + column // 8]
            address = 0x9000 + (tile if tile < 128 else tile - 256) * 16 + row % 8 * 2
            bit = 7 - column % 8
            actual = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
            assert actual == expected.getpixel((column, row)), f"pause template or live Itty Bitty text differs at {column},{row}"


def check_pause_menu(emulator, output):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    before = bytes(emulator.memory[board:board + 37])
    scores = SYMBOLS["_score_table"]
    selected = 0

    def select(target):
        nonlocal selected
        while selected != target:
            press(emulator, "down")
            selected = (selected + 1) % 5

    try:
        for sound in (0, 1):
            select(2)
            if emulator.memory[scores + 50] != sound:
                press(emulator, "a")
            for reduced in (0, 1):
                select(3)
                if emulator.memory[scores + 51] != reduced:
                    press(emulator, "a")
                for selection in range(5):
                    select(selection)
                    check_pause_screen(emulator, selection)
                    assert bytes(emulator.memory[board:board + 37]) == before, "pause navigation changed the board or score"
                    emulator.screen.image.save(output.with_name(f"{output.stem}-{selection}-{sound}-{reduced}.png"))
        select(0)
        press(emulator, "up")
        check_pause_screen(emulator, 4)
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_settings_screen(emulator, selection):
    scores = SYMBOLS["_score_table"]
    sound = emulator.memory[scores + 50]
    full_flash = not emulator.memory[scores + 51]
    with Image.open(ROOT / "assets/settings_master.png") as master:
        source = master.convert("RGB").resize((160, 144), Image.Resampling.LANCZOS)
    quantized = source.quantize(colors=4, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    palette = [tuple(quantized.getpalette()[index * 3:index * 3 + 3]) for index in range(4)]
    palette.sort(key=lambda color: color[0] * 299 + color[1] * 587 + color[2] * 114, reverse=True)
    expected = Image.new("L", (160, 144))
    expected.putdata([min(range(4), key=lambda shade: sum((channel - target) ** 2 for channel, target in zip(color, palette[shade]))) for color in source.getdata()])
    draw = ImageDraw.Draw(expected)
    draw.rectangle((80, 62, 147, 111), fill=expected.getpixel((130, 104)))
    draw.rectangle((20, 131, 142, 142), fill=0)
    for row, (label, enabled) in enumerate((("SOUND", sound), ("FLASH", full_flash))):
        top = 64 + row * 16
        if row == selection:
            draw.rectangle((80, top, 143, top + 11), fill=0)
            draw.polygon(((82, top + 3), (85, top + 6), (82, top + 9)), fill=3)
        for text, left in ((label, 89), ("ON" if enabled else "OFF", 125)):
            for character in text:
                glyph = HIGHSCORE_GLYPHS[character]
                for glyph_row in range(8):
                    for glyph_column in range(glyph.width):
                        if glyph.getpixel((glyph_column, glyph_row)):
                            expected.putpixel((left + glyph_column, top + 2 + glyph_row), 3)
                left += glyph.width + 1
    assert emulator.memory[SYMBOLS["_screen_state"]] == 12
    assert emulator.memory[0xFF40] & 0x80 and not emulator.memory[0xFF40] & 0x12, "settings lost its background mode or retained sprites"
    assert emulator.memory[0xFF42] == emulator.memory[0xFF43] == 0, "settings inherited gameplay scrolling"
    for row in range(144):
        for column in range(160):
            tile = emulator.memory[0x9800 + row // 8 * 32 + column // 8]
            address = 0x9000 + (tile if tile < 128 else tile - 256) * 16 + row % 8 * 2
            bit = 7 - column % 8
            actual = (emulator.memory[address] >> bit & 1) | ((emulator.memory[address + 1] >> bit & 1) << 1)
            assert actual == expected.getpixel((column, row)), f"settings art, Itty Bitty text, selection or blank footer differs at {column},{row}"


def check_start_menu(emulator, output, cgb):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    scores = SYMBOLS["_score_table"]
    try:
        for selection in range(4):
            check_start_menu_selection(emulator, selection)
            emulator.screen.image.save(output.with_name(f"{output.stem}-{selection}.png"))
            press(emulator, "down")
            emulator.tick(10)
        check_start_menu_selection(emulator, 0)
        press(emulator, "up")
        check_start_menu_selection(emulator, 3)
        press(emulator, "down")
        press(emulator, "down")
        press(emulator, "a")
        wait_screen(emulator, 12)
        sound = emulator.memory[scores + 50]
        reduced = emulator.memory[scores + 51]
        check_settings_screen(emulator, 0)
        press(emulator, "a")
        assert list(emulator.memory[scores + 50:scores + 52]) == [sound, reduced], "A unexpectedly changed settings instead of Left/Right"
        for sound_enabled in (0, 1):
            press(emulator, "right" if sound_enabled else "left")
            assert emulator.memory[scores + 50] == sound_enabled, "Left/Right did not set sound off/on"
            for flash_enabled in (0, 1):
                press(emulator, "down")
                press(emulator, "right" if flash_enabled else "left")
                assert emulator.memory[scores + 51] == (not flash_enabled), "Left/Right did not set flashing off/on"
                check_settings_screen(emulator, 1)
                emulator.screen.image.save(output.with_name(f"{output.stem}-settings-{sound_enabled}-{flash_enabled}.png"))
                press(emulator, "up")
                check_settings_screen(emulator, 0)
        generation = bytes(emulator.memory[scores + 52:scores + 54])
        press(emulator, "right", 30)
        assert bytes(emulator.memory[scores + 52:scores + 54]) == generation, "holding an already-enabled setting rewrites SRAM"
        press(emulator, "left" if sound else "right")
        assert emulator.memory[scores + 50] == sound ^ 1, "menu sound setting did not change"
        press(emulator, "down")
        press(emulator, "right" if reduced else "left")
        assert emulator.memory[scores + 51] == reduced ^ 1, "menu flash setting did not change"
        check_settings_screen(emulator, 1)
        emulator.screen.image.save(output.with_name(f"{output.stem}-settings.png"))
        restarted = boot(cgb, saved_ram(emulator))
        try:
            assert restarted.memory[scores + 50] == sound ^ 1, "menu sound setting was not saved"
            assert restarted.memory[scores + 51] == reduced ^ 1, "menu flash setting was not saved"
        finally:
            restarted.stop(save=False)
        press(emulator, "left" if reduced else "right")
        press(emulator, "up")
        press(emulator, "right" if sound else "left")
        press(emulator, "b")
        wait_screen(emulator, 11)
        check_start_menu_selection(emulator, 1)
        press(emulator, "down")
        press(emulator, "down")
        press(emulator, "a")
        wait_screen(emulator, 1)
        emulator.tick(2)
        check_highscore_panel(emulator, 0)
        check_highscore_animation(emulator)
        fixed_art = emulator.screen.image.crop((0, 0, 80, 128)).tobytes()
        emulator.screen.image.save(output.with_name(f"{output.stem}-high-scores.png"))
        press(emulator, "right")
        emulator.tick(90)
        check_highscore_panel(emulator, 1)
        assert not emulator.memory[0xFF40] & 2, "highest-score animation leaked onto page two"
        assert emulator.screen.image.crop((0, 0, 80, 128)).tobytes() == fixed_art, "paging changed the high-score mascot/header"
        emulator.screen.image.save(output.with_name(f"{output.stem}-high-scores-page-2.png"))
        press(emulator, "left")
        emulator.tick(90)
        check_highscore_panel(emulator, 0)
        press(emulator, "b")
        wait_screen(emulator, 11)
        check_start_menu_selection(emulator, 3)
        press(emulator, "up")
        press(emulator, "a")
        wait_screen(emulator, 3)
        press(emulator, "b")
        wait_screen(emulator, 11)
        check_start_menu_selection(emulator, 2)
        press(emulator, "b")
        wait_screen(emulator, 0)
        emulator.button_press("start")
        emulator.tick(90)
        assert emulator.memory[SYMBOLS["_screen_state"]] == 11, "held title Start also activated Play"
        emulator.button_release("start")
        emulator.tick(3)
        press(emulator, "start")
        wait_screen(emulator, 4)
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def check_chain_stars(emulator, cgb, output):
    snapshot = BytesIO()
    emulator.save_state(snapshot)
    board = SYMBOLS["_game_state"]
    active = static_address("ui", "chain_stars_active")
    age = static_address("ui", "chain_star_age")
    reduced = static_address("ui", "reduced_flash")
    shadow = SYMBOLS["_shadow_OAM"]
    base = int(re.search(r"#define ART_CHAIN_STAR_BASE (\d+)u", ART_HEADER).group(1))
    source = INVALID_SOURCE.split("const uint8_t chain_star_tiles[] = {", 1)[1].split("};", 1)[0]
    star_tiles = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", source))
    dmg_source = INVALID_SOURCE.split("const uint8_t chain_star_dmg_tiles[] = {", 1)[1].split("};", 1)[0]
    dmg_star_tiles = bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", dmg_source))

    def prepare(origin, low_flash):
        snapshot.seek(0)
        emulator.load_state(snapshot)
        emulator.memory[board:board + 25] = [0] * 25
        neighbors, upgrades = {
            12: ((11, 13), (7, 17)),
            5: ((0, 10), (6, 7)),
            21: ((20, 22), (16, 17)),
        }[origin]
        for index in neighbors:
            emulator.memory[board + index] = 1
        for index in upgrades:
            emulator.memory[board + index] = 2
        emulator.memory[board + 25:board + 37] = [1, 0, 1, origin % 5, origin // 5, 0, 0, 0, 0, 0, 0, 0]
        emulator.memory[reduced] = low_flash
        press(emulator, "b")
        emulator.tick(40)
        press(emulator, "a")

    try:
        for origin, low_flash in ((12, 0), (5, 0), (21, 0), (12, 1)):
            prepare(origin, low_flash)
            positions = set()
            variants = set()
            bursts = set()
            active_frames = 0
            clipped = False
            saved = False
            for _ in range(360):
                emulator.tick()
                if not emulator.memory[active]:
                    continue
                active_frames += 1
                assert not low_flash, "reduced flashing enabled chain firecrackers"
                current_age = emulator.memory[age]
                assert current_age <= 60, "star clock ran past one second"
                if current_age < 2 or current_age >= 60:
                    continue
                bursts.add(current_age // 20)
                expected_star_tiles = star_tiles if cgb else dmg_star_tiles
                assert bytes(emulator.memory[0x8000 + base * 16:0x8000 + base * 16 + len(expected_star_tiles)]) == expected_star_tiles, "chain star art overwritten"
                sprites = [tuple(emulator.memory[0xFE00 + index * 4:0xFE00 + index * 4 + 4]) for index in range(38)]
                for star in range(1):
                    sprite_y, sprite_x, tile, prop = sprites[star * 2]
                    right_y, right_x, right_tile, right_prop = sprites[star * 2 + 1]
                    assert tile == base, "stars collided with score or multiplier tiles"
                    assert right_tile == base + 2, "star right half is missing"
                    assert prop in ((3, 4) if cgb else (0x10,)), "star palette is incorrect"
                    assert right_prop == prop, "star halves use different palettes"
                    variants.add(tile)
                    if not sprite_x and not sprite_y:
                        clipped = True
                        assert not right_x and not right_y, "clipped star right half remains visible"
                    else:
                        assert 9 <= sprite_x <= 159 and 17 <= sprite_y <= 151, "star wrapped around a screen edge"
                        assert (right_y, right_x) == (sprite_y, sprite_x + 8), "star right half is displaced"
                if cgb:
                    for scanline in range(144):
                        assert sum(sprite_x and sprite_y and sprite_y - 16 <= scanline < sprite_y for sprite_y, sprite_x, _, _ in sprites) <= 10, "firecrackers exceed the hardware scanline limit"
                positions.add(tuple(sprite[:2] for sprite in sprites[:2]))
                assert not visible_callout(emulator), "chain burst showed an exclamation word"
                if current_age >= 10 and not saved:
                    emulator.screen.image.save(output / f"{'cgb' if cgb else 'dmg'}-chain-stars-{origin}.png")
                    saved = True
            for _ in range(2):
                if not emulator.memory[active]:
                    break
                emulator.tick()
            assert not emulator.memory[active], f"stars did not expire (age={emulator.memory[age]}, reduced={low_flash})"
            assert all(emulator.memory[shadow + index * 4] == 0 for index in range(2)), "expired stars remain in OAM"
            if not low_flash:
                assert 57 <= active_frames <= 63, f"stars lasted {active_frames} frames, not one second"
                assert bursts == {0, 1, 2} and len(positions) >= 6, f"firecracker trajectories did not animate: bursts={bursts}, positions={len(positions)}"
                assert variants == {base}, "chain star tile changed during the burst"
                if origin != 12:
                    assert clipped, "edge burst did not exercise clipping"
            assert emulator.memory[board + origin] == 3, "chain mechanics changed"

        prepare(12, 0)
        for _ in range(300):
            emulator.tick()
            if emulator.memory[active] and emulator.memory[age] >= 5:
                break
        else:
            raise AssertionError("chain stars never started")
        cursor = emulator.memory[board + 28]
        press(emulator, "right")
        assert emulator.memory[board + 28] == cursor + 1, "firecrackers block movement"
        assert emulator.memory[active], "movement cancelled the firecrackers"
        burst_snapshot = BytesIO()
        emulator.save_state(burst_snapshot)
        press(emulator, "start")
        wait_screen(emulator, 5)
        assert not emulator.memory[active], "firecrackers leaked into pause"
        burst_snapshot.seek(0)
        emulator.load_state(burst_snapshot)
        emulator.memory[board:board + 25] = [0] * 25
        for index in (11, 13):
            emulator.memory[board + index] = 1
        emulator.memory[board + 25:board + 37] = [1, 0, 1, 2, 2, 0, 0, 0, 0, 0, 0, 0]
        assert emulator.memory[active], "burst ended before the interruption test"
        press(emulator, "a")
        emulator.tick(10)
        assert not emulator.memory[active], "new merge did not release the star sprites"
        assert not any(
            emulator.memory[0xFE00 + sprite * 4]
            and CHAIN_REACTION_BASE <= emulator.memory[0xFE00 + sprite * 4 + 2] < CHAIN_REACTION_BASE + CHAIN_REACTION_TILES
            for sprite in range(4, 4 + CHAIN_REACTION_SPRITES)
        ), "new merge left fragments of the prior chain badge in OAM"
        emulator.tick(200)
        assert emulator.memory[board + 12] == 2, "new merge failed during a firecracker burst"
        assert all(emulator.memory[shadow + index * 4] == 0 for index in range(2)), "star/score sprites remain after the new merge"
    finally:
        snapshot.seek(0)
        emulator.load_state(snapshot)


def run(cgb):
    name = "cgb" if cgb else "dmg"
    output = ROOT / "build/screenshots"
    output.mkdir(parents=True, exist_ok=True)
    emulator = boot(cgb)
    chain_timer = static_address("ui", "chain_reaction_timer")
    try:
        assert emulator.memory[SYMBOLS["_screen_state"]] == 9, "startup intro was not displayed"
        check_intro_version(emulator)
        check_screen_boundary(emulator)
        emulator.screen.image.save(output / f"{name}-intro.png")
        wait_screen(emulator, 0)
        assert emulator.memory[0xFF40] & 0x02, "title prompt was not visible immediately"
        assert title_prompt_visible(emulator), "title prompt was not visible immediately"
        wait_title_prompt(emulator, False, 35)
        emulator.tick()
        title_background = emulator.screen.image.copy()
        for visible in (True, False, True):
            frames = 0
            while title_prompt_visible(emulator) != visible and frames < 35:
                emulator.tick()
                frames += 1
            assert 28 <= frames <= 31, f"title blink interval was {frames} frames instead of half a second"
        emulator.tick()
        check_title_prompt(emulator, title_background)
        check_screen_boundary(emulator)
        emulator.screen.image.save(output / f"{name}-title.png")
        wait_title_prompt(emulator, False)
        emulator.tick()
        assert emulator.screen.image.tobytes() == title_background.tobytes(), "hidden prompt left pixels on the title artwork"
        wait_title_prompt(emulator, True)
        seen_screens = set()
        for _ in range(1250):
            emulator.tick()
            seen_screens.add(emulator.memory[SYMBOLS["_screen_state"]])
        assert seen_screens >= {0, 1, 2}, seen_screens
        if emulator.memory[SYMBOLS["_screen_state"]] == 2:
            press(emulator, "b")
            wait_screen(emulator, 0)
        press(emulator, "b")
        wait_screen(emulator, 2)
        emulator.tick(60)
        fading_credits = emulator.screen.image.tobytes()
        emulator.screen.image.save(output / f"{name}-credits.png")
        emulator.tick(120)
        emulator.screen.image.save(output / f"{name}-credits-faded.png")
        assert emulator.screen.image.tobytes() != fading_credits, "credits text did not fade between groups"
        press(emulator, "start")
        wait_screen(emulator, 11)
        check_start_menu(emulator, output / f"{name}-start-menu.png", cgb)
        press(emulator, "down")
        press(emulator, "down")
        press(emulator, "a")
        wait_screen(emulator, 3)
        emulator.screen.image.save(output / f"{name}-instructions.png")
        check_instruction_page(emulator, 0)
        for page in range(1, INSTRUCTION_PAGES):
            press(emulator, "right")
            check_instruction_page(emulator, page)
            emulator.screen.image.save(output / f"{name}-instructions-{page + 1}.png")
        press(emulator, "right")
        check_instruction_page(emulator, 0)
        press(emulator, "left")
        check_instruction_page(emulator, INSTRUCTION_PAGES - 1)
        for page in range(INSTRUCTION_PAGES - 2, -1, -1):
            press(emulator, "left")
            check_instruction_page(emulator, page)
        press(emulator, "a")
        wait_screen(emulator, 11)
        press(emulator, "up")
        press(emulator, "up")
        spiral_frames = []
        spiral_cache = static_address("ui", "cell_cache")

        def capture_spiral(_):
            if not emulator.memory[static_address("ui", "hover_enabled")]:
                spiral_frames.append(tuple(index for index in range(25) if emulator.memory[spiral_cache + index] == 8))

        emulator.hook_register(0, SYMBOLS["_service_animation_input"], capture_spiral, None)
        press(emulator, "a")
        wait_screen(emulator, 4)
        center_before_hover = emulator.screen.image.crop((45, 62, 65, 82)).tobytes()
        assert not emulator.memory[static_address("ui", "hover_enabled")], "hover flashing began before the opening spiral finished"
        assert any(NEXT_DICE_BASE <= emulator.memory[0x9800 + row * 32 + column] < NEXT_DICE_BASE + 32 for row in range(8, 12) for column in range(14, 18)), "next-piece dice were hidden during the opening spiral"
        emulator.tick(180)
        emulator.hook_deregister(0, SYMBOLS["_service_animation_input"])
        expected_spiral = (20, 15, 10, 5, 0, 1, 2, 3, 4, 9, 14, 19, 24, 23, 22, 21, 16, 11, 6, 7, 8, 13, 18, 17, 12)
        assert spiral_frames == [tuple(sorted(expected_spiral[index:index + 2])) for index in range(0, len(expected_spiral), 2)], "opening ripple must hold paired cells for one frame, bottom-left to center"
        center_after_hover = emulator.screen.image.crop((45, 62, 65, 82)).tobytes()
        assert center_after_hover != center_before_hover, "hovering dice did not appear after the center pulse"
        assert emulator.memory[0xFF42] == 234 and emulator.memory[0xFF43] == 251, "grid did not receive the approved (5, 22) position"
        screen = emulator.screen.image
        background = screen.getpixel((5, 6))
        check_screen_boundary(emulator)
        check_game_mascot(emulator, cgb)
        dot = screen.getpixel((6, 7))
        assert dot != background, "outer background pattern is invisible"
        assert all(screen.getpixel((column, row)) == (dot if ((column - 5) % 8, (row - 22) % 8) in ((1, 1), (5, 5)) else background) for row in range(6, 22) for column in range(5, 109)), "top inset contains wrapped tiles instead of the dotted pattern"
        assert screen.getpixel((20, 22)) != background and screen.getpixel((5, 37)) != background, "grid rails do not start at (5, 22)"
        assert screen.getpixel((104, 37)) != background and screen.getpixel((20, 121)) != background, "inset clipped the 100x100 grid"
        for grid_row in range(5):
            for grid_column in range(5):
                cell_left = 5 + grid_column * 20
                cell_top = 22 + grid_row * 20
                assert screen.getpixel((cell_left, cell_top + 8)) != background, "grid column spacing is not 20 pixels"
                assert screen.getpixel((cell_left + 8, cell_top)) != background, "grid row spacing is not 20 pixels"
        assert all(
            screen.getpixel((column, row)) != background
            for column in (153, 155)
            for row in range(84, 119)
        ), "preview window lost an inner or outer right border"
        assert emulator.memory[0x9800 + 12 * 32 + 12] != 0, "100x100 board canvas was not drawn"
        assert all(
            emulator.memory[0x9800 + row * 32 + column] == 255
            for row in (13, 14, 16, 17)
            for column in range(19)
        ), "board or preview replaced the pattern below the playing area"
        assert all(
            emulator.memory[0x9800 + row * 32 + column] == 255
            for row in range(13, 15)
            for column in range(13, 19)
        ), "space below the preview window lost its pattern"
        assert any(
            emulator.memory[0x9800 + row * 32 + column] != 0
            for row in range(6, 13)
            for column in range(13, 19)
        ), "preview-window artwork was not drawn next to the board"
        if cgb:
            emulator.memory[0xFF4F] = 1
            assert all(
                emulator.memory[0x9800 + row * 32 + column] == (2 if row == 15 or (column == 19 and row < 16) else 4 if 13 <= column < 19 and (row < 3 or 7 <= row < 13) else 1 if column < 13 and row < 13 else 3)
                for row in range(18)
                for column in range(20)
            ), "grid, background and black boundary palettes were not applied separately"
            assert all(emulator.memory[0x9800 + 31 * 32 + column] == 4 for column in range(13, 19)), "raised score header lost its panel palette"
            emulator.memory[0xFF4F] = 0
        emulator.screen.image.save(output / f"{name}-game.png")
        check_gameplay_hud(emulator)
        check_score_updates(emulator)
        check_native_board_dice(emulator, output / f"{name}-filled-grid.png")
        check_hover_flash(emulator)
        check_native_preview_dice(emulator, output / f"{name}-preview.png")
        check_invalid_preview(emulator, output / f"{name}-invalid-preview.png")
        check_atari_effects(emulator)
        check_flying_scores(emulator, cgb, output / f"{name}-score-flight.png")
        check_chain_stars(emulator, cgb, output)
        board = SYMBOLS["_game_state"]
        count = emulator.memory[board + 27]
        press(emulator, "a", 30)
        emulator.tick(80)
        assert sum(bool(value) for value in emulator.memory[board:board + 25]) == count, "held A places more than once"
        press(emulator, "start")
        wait_screen(emulator, 5)
        assert emulator.memory[0xFF42] == 0 and emulator.memory[0xFF43] == 0, "gameplay inset leaked into the pause screen"
        emulator.screen.image.save(output / f"{name}-pause.png")
        check_pause_menu(emulator, output / f"{name}-pause.png")
        press(emulator, "down")
        press(emulator, "a")
        wait_screen(emulator, 3)
        check_instruction_page(emulator, 0)
        press(emulator, "b")
        wait_screen(emulator, 5)
        check_pause_screen(emulator, 1)
        press(emulator, "up")
        for _ in range(4):
            press(emulator, "down")
        press(emulator, "a")
        wait_screen(emulator, 8)
        press(emulator, "b")
        wait_screen(emulator, 5)
        check_pause_screen(emulator, 4)
        press(emulator, "b")
        wait_screen(emulator, 4)
        emulator.memory[board:board + 25] = [0] * 25
        for index, value in ((11, 1), (13, 1), (7, 2), (17, 2)):
            emulator.memory[board + index] = value
        emulator.memory[board + 25:board + 37] = [1, 0, 1, 2, 2, 0, 0, 0, 0, 0, 0, 0]
        art_before_chain = static_gameplay_art(emulator)
        press(emulator, "a")
        callout_seen = False
        chain_reaction_seen = False
        chain_gameplay_continued = False
        chain_reaction_frames = 0
        for _ in range(360):
            emulator.tick()
            chain_reaction_visible = emulator.memory[chain_timer] and emulator.memory[0xFF40] & 0x02 and any(
                emulator.memory[0xFE00 + sprite * 4]
                and CHAIN_REACTION_BASE <= emulator.memory[0xFE00 + sprite * 4 + 2] < CHAIN_REACTION_BASE + CHAIN_REACTION_TILES
                for sprite in range(4, 4 + CHAIN_REACTION_SPRITES)
            )
            if chain_reaction_visible and emulator.memory[board + 34] >= 2:
                chain_reaction_frames += 1
                if not chain_reaction_seen:
                    chain_reaction_seen = True
                    assert bytes(emulator.memory[0x8000 + CHAIN_REACTION_BASE * 16:0x8000 + (CHAIN_REACTION_BASE + CHAIN_REACTION_TILES) * 16]) == CHAIN_REACTION_BYTES, "chain badge tiles were not loaded during VBlank"
                    assert emulator.memory[0xFF40] & 0x04, "chain badge is not using the callout 8x16 sprite format"
                    assert static_gameplay_art(emulator) == art_before_chain, "chain sprite corrupted grid or preview tiles"
                    assert not visible_callout(emulator), "exclamation callout appeared during a chain reaction"
                    emulator.tick(6)
                    chain_reaction_frames += 6
                    cursor_x = emulator.memory[board + 28]
                    press(emulator, "right")
                    chain_reaction_frames += 8
                    assert emulator.memory[board + 28] == cursor_x + 1, "gameplay paused behind the chain reaction sprite"
                    assert emulator.memory[0xFF40] & 0x02, "chain reaction sprite disappeared while gameplay continued"
                    chain_gameplay_continued = True
                    emulator.screen.image.save(output / f"{name}-chain-reaction.png")
            if not callout_seen and visible_callout(emulator):
                callout_seen = True
                emulator.tick(2)
                assert visible_callout(emulator), "grid callout disappeared before it could be displayed"
                check_score_panel(emulator)
                emulator.screen.image.save(output / f"{name}-callout.png")
        assert not callout_seen, "exclamation callout appeared during a chain reaction"
        assert chain_reaction_seen, "chain reaction sprite was not displayed"
        assert chain_gameplay_continued, "chain reaction sprite blocked gameplay"
        assert chain_reaction_frames >= 55, "chain reaction sprite was not held for one second"
        assert static_gameplay_art(emulator) == art_before_chain, "merge effects overwrote static gameplay artwork"
        assert emulator.memory[board + 12] == 3
        assert emulator.memory[board + 35] == 15
        emulator.screen.image.save(output / f"{name}-chain.png")
        emulator.memory[board:board + 25] = [0] * 25
        for index in (11, 13, 17):
            emulator.memory[board + index] = 6
        emulator.memory[board + 25:board + 37] = [6, 0, 1, 2, 2, 0, 0, 0, 0, 0, 8, 7]
        refreshed_after_clear = []
        emulator.hook_register(0, SYMBOLS["_ui_refresh_game"], lambda flag: flag.append(True), refreshed_after_clear)
        press(emulator, "a")
        emulator.tick(35)
        emulator.screen.image.save(output / f"{name}-six-clear.png")
        for _ in range(600):
            if refreshed_after_clear:
                break
            emulator.tick()
        assert refreshed_after_clear, "six-clear animation never returned to gameplay"
        emulator.hook_deregister(0, SYMBOLS["_ui_refresh_game"])
        emulator.tick(20)
        assert emulator.memory[board + 32] == 1
        assert emulator.memory[board + 35] | (emulator.memory[board + 36] << 8) == 1924
        assert not any(emulator.memory[board:board + 25])
        check_screen_boundary(emulator)
        press(emulator, "start")
        wait_screen(emulator, 5)
        press(emulator, "down")
        press(emulator, "down")
        press(emulator, "a")
        press(emulator, "down")
        press(emulator, "a")
        press(emulator, "b")
        wait_screen(emulator, 4)
        emulator.memory[board:board + 25] = [(index % 5 + index // 5) % 6 + 1 for index in range(25)]
        emulator.memory[board + 24] = 0
        emulator.memory[board + 25:board + 35] = [1, 0, 1, 4, 4, 0, 0, 1, 0, 0]
        press(emulator, "a")
        wait_screen(emulator, 6)
        check_screen_boundary(emulator)
        assert all(not 1 <= emulator.memory[0x9800 + row * 32 + column] < 40 for row in range(15, 18) for column in range(20)), "game-over text was not removed"
        emulator.screen.image.save(output / f"{name}-game-over.png")
        check_game_over_flow(emulator)
        press(emulator, "a")
        wait_screen(emulator, 10)
        check_screen_boundary(emulator)
        check_result_numbers(emulator, 1924, 1924)
        emulator.screen.image.save(output / f"{name}-results.png")
        press(emulator, "down")
        emulator.screen.image.save(output / f"{name}-results-main-menu.png")
        press(emulator, "a")
        wait_screen(emulator, 7)
        check_highscore_panel(emulator, 0)
        press(emulator, "up")
        press(emulator, "a")
        press(emulator, "up")
        press(emulator, "up")
        press(emulator, "a")
        press(emulator, "up")
        press(emulator, "up")
        press(emulator, "up")
        emulator.screen.image.save(output / f"{name}-initials.png")
        press(emulator, "start")
        wait_screen(emulator, 11)
        emulator.tick(20)
        emulator.screen.image.save(output / f"{name}-start-menu-after-results.png")
        ram = saved_ram(emulator)
        for corrupt in (False, True):
            restored = bytearray(ram)
            if corrupt:
                restored[0x180] ^= 1
            restarted = boot(cgb, restored)
            try:
                scores = SYMBOLS["_score_table"]
                assert restarted.memory[scores + 50] == 0
                assert restarted.memory[scores + 51] == 1
                top = restarted.memory[scores + 3] | restarted.memory[scores + 4] << 8
                assert top == (1349 if corrupt else 1924), top
                if not corrupt:
                    assert bytes(restarted.memory[scores:scores + 3]) == b"BCD", (bytes(restarted.memory[scores:scores + 3]), hex(emulator.memory[0xFF40]), hex(emulator.register_file.PC))
            finally:
                restarted.stop(save=False)
        cheater = boot(cgb)
        try:
            press(cheater, "start")
            wait_screen(cheater, 0)
            press(cheater, "start")
            wait_screen(cheater, 11)
            press(cheater, "a")
            wait_screen(cheater, 4)
            cheater.tick(120)
            for button in ("up", "up", "down", "down", "left", "right", "left", "right", "b", "a"):
                press(cheater, button)
            wait_screen(cheater, 6)
        finally:
            cheater.stop(save=False)
        print(f"{name}: screens, input, chains, six-clear, cheat, initials, settings and save recovery passed")
    finally:
        emulator.stop(save=False)


if __name__ == "__main__":
    run(False)
    run(True)
