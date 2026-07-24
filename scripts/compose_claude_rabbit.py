from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SCREEN_PATH = Path(r"C:\Users\10735\AppData\Local\Temp\codex-clipboard-5e053782-75bd-4a45-9a25-60a8c483d37b.png")
RABBIT_PATH = Path(r"C:\Users\10735\AppData\Local\Temp\codex-clipboard-3ae59662-e30c-4138-b0ae-65f1e7f1e1dd.png")
OUT = ROOT / "output" / "imagegen"
OUT.mkdir(parents=True, exist_ok=True)


def rabbit_layers():
    source = Image.open(RABBIT_PATH).convert("RGB")
    # Tight subject bounds measured from the supplied 1254px reference.
    crop = source.crop((320, 303, 934, 958))
    rgb = np.asarray(crop, dtype=np.int16)
    background = np.asarray(source.getpixel((30, 30)), dtype=np.int16)
    distance = np.max(np.abs(rgb - background), axis=2)

    # Keep the sepia linework and pencil shading, but do not use it as the fill mask.
    ink_alpha = np.clip((distance.astype(np.float32) - 5.0) * (255.0 / 22.0), 0, 255)
    ink_alpha = Image.fromarray(ink_alpha.astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(0.25))
    ink = crop.convert("RGBA")
    ink.putalpha(ink_alpha)

    # The light bunny interior is intentionally filled with warm cream so it stays
    # opaque on the black terminal background.
    silhouette = Image.new("L", crop.size, 0)
    draw = ImageDraw.Draw(silhouette)
    draw.ellipse((98, 4, 430, 205), fill=255)  # cap
    draw.polygon([(112, 102), (38, 145), (3, 330), (18, 445), (86, 475), (160, 360), (177, 205)], fill=255)
    draw.polygon([(380, 105), (485, 145), (606, 290), (590, 384), (535, 410), (463, 325), (418, 182)], fill=255)
    draw.ellipse((105, 112, 510, 431), fill=255)  # head
    draw.ellipse((120, 348, 520, 654), fill=255)  # body
    draw.ellipse((70, 426, 184, 590), fill=255)  # tail
    draw.ellipse((190, 525, 325, 654), fill=255)  # left foot
    draw.ellipse((335, 525, 480, 654), fill=255)  # right foot
    silhouette = silhouette.filter(ImageFilter.GaussianBlur(0.8))

    fill = Image.new("RGBA", crop.size, (247, 231, 201, 0))
    fill.putalpha(silhouette)
    filled = Image.alpha_composite(fill, ink)
    filled.save(OUT / "claude-code-rabbit-cutout-filled.png")
    return filled


def fit_inside(image, box):
    scale = min(box[0] / image.width, box[1] / image.height)
    size = (round(image.width * scale), round(image.height * scale))
    return image.resize(size, Image.Resampling.LANCZOS)


def compose():
    screen = Image.open(SCREEN_PATH).convert("RGBA")
    rabbit = fit_inside(rabbit_layers(), (104, 108))

    # Clear the original orange Claude pixel mark inside the welcome panel.
    draw = ImageDraw.Draw(screen)
    draw.rectangle((184, 389, 321, 505), fill=(10, 10, 10, 255))
    screen.alpha_composite(rabbit, (204, 391))

    output = OUT / "claude-code-rabbit-final.png"
    screen.convert("RGB").save(output, optimize=True)
    print(output)


if __name__ == "__main__":
    compose()
