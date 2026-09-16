from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PALETTE = ((229, 240, 183), (139, 172, 15), (48, 98, 48), (13, 56, 0))


def restore_outline_edges(die):
    for row in (0, 17):
        for column in range(18):
            color = die.getpixel((column, row))
            if color[3]:
                die.putpixel((column, row), (*color[:3], 255))


def rebuild_die(filename, pips, frame="four_18x18.png"):
    with Image.open(ROOT / "assets/dice" / frame) as master:
        if master.size != (18, 18):
            raise ValueError(f"expected native 18x18 style reference: {frame}")
        die = master.convert("RGBA")
    if frame == "four_18x18.png":
        restore_outline_edges(die)
    draw = ImageDraw.Draw(die)
    draw.rectangle((3, 3, 14, 14), fill=(*PALETTE[1], 255))
    for left, top in pips:
        draw.rectangle((left, top, left + 2, top + 2), fill=(*PALETTE[3], 255))
    die.save(ROOT / "assets/dice" / filename)
