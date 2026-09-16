from itertools import permutations

from PIL import Image, ImageDraw

from dice_frame import PALETTE


SHADE_PERMUTATIONS = tuple(permutations(range(4)))
FACE_SHADES = (
    (1, 0, 2, 3),
    (0, 1, 2, 3),
    (3, 2, 1, 0),
    (2, 3, 1, 0),
    (3, 0, 1, 2),
    (0, 3, 2, 1),
)


def shade_die(indexed, source, mapping):
    result = indexed.copy()
    result.putdata([
        mapping[shade] if color[3] >= 128 else 0
        for shade, color in zip(indexed.getdata(), source.getdata())
    ])
    return result


def save_shading_previews(native_dice, native_sources, directory):
    sheet = Image.new("RGB", (672, 1056), PALETTE[0])
    draw = ImageDraw.Draw(sheet)
    for index, mapping in enumerate(SHADE_PERMUTATIONS):
        left = index % 3 * 224
        top = index // 3 * 132
        draw.text((left + 8, top + 4), f"{index + 1:02d}: {''.join(map(str, mapping))}", fill=PALETTE[3])
        for face in range(6):
            die = shade_die(native_dice[face], native_sources[face], mapping)
            preview = Image.new("RGB", die.size)
            preview.putdata([PALETTE[shade] for shade in die.getdata()])
            sheet.paste(preview.resize((54, 54), Image.Resampling.NEAREST),
                        (left + 60 + face % 3 * 54, top + 24 + face // 3 * 54))
    sheet.save(directory / "dice-24-shadings.png")
    selected = Image.new("RGB", (648, 128), PALETTE[0])
    draw = ImageDraw.Draw(selected)
    for face, mapping in enumerate(FACE_SHADES):
        die = shade_die(native_dice[face], native_sources[face], mapping)
        preview = Image.new("RGB", die.size)
        preview.putdata([PALETTE[shade] for shade in die.getdata()])
        selected.paste(preview.resize((108, 108), Image.Resampling.NEAREST), (face * 108, 20))
        draw.text((face * 108 + 8, 4), f"Face {face + 1}: #{SHADE_PERMUTATIONS.index(mapping) + 1:02d}", fill=PALETTE[3])
    selected.save(directory / "dice-selected-shadings.png")
