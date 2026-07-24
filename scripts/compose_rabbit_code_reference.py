from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCREEN = Path(r"C:\Users\10735\Desktop\提示词\download.png")
SOURCE_RABBIT = Path(r"C:\Users\10735\Desktop\提示词\兔兔素材.png")
OUTPUT_DIR = ROOT / "output" / "imagegen"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def make_cutout():
    image = Image.open(SOURCE_RABBIT).convert("RGBA")
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    background = rgb[30, 30]
    distance = np.max(np.abs(rgb - background), axis=2)

    # Remove the nearly uniform paper while retaining the light pencil shading.
    alpha = np.clip((distance.astype(np.float32) - 5.0) * (255.0 / 18.0), 0, 255)
    alpha = Image.fromarray(alpha.astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(0.35))
    image.putalpha(alpha)

    # The supplied paper has low-frequency texture that can create faint alpha
    # values far outside the subject, so use the measured subject bounds.
    bbox = (320, 303, 934, 958)
    cutout = image.crop(bbox)
    cutout.save(OUTPUT_DIR / "rabbit-code-rabbit-cutout.png")
    return cutout, image.crop((320, 310, 925, 810))


def fit_inside(image, box):
    width, height = image.size
    target_width, target_height = box
    scale = min(target_width / width, target_height / height)
    size = (round(width * scale), round(height * scale))
    return image.resize(size, Image.Resampling.LANCZOS)


def compose(screen, rabbit, icon_source):
    result = screen.convert("RGBA")

    # Clear the original hero bunny with the surrounding paper tone before placing the new source.
    paper_color = result.getpixel((700, 100))
    background = Image.new("RGBA", result.size, paper_color)
    erase_mask = Image.new("L", result.size, 0)
    erase_draw = ImageDraw.Draw(erase_mask)
    erase_draw.rectangle((700, 92, 1050, 468), fill=255)
    erase_mask = erase_mask.filter(ImageFilter.GaussianBlur(14))
    result = Image.composite(background, result, erase_mask)

    main_rabbit = rabbit.resize((310, 331), Image.Resampling.LANCZOS)
    result.alpha_composite(main_rabbit, (740, 116))

    # The original logo is replaced with a clean patch before the new source icon is placed.
    patch_color = result.getpixel((80, 12))
    draw = ImageDraw.Draw(result)
    draw.rectangle((22, 17, 66, 66), fill=patch_color)

    logo = fit_inside(icon_source, (39, 39))
    logo_canvas = Image.new("RGBA", (39, 39), (0, 0, 0, 0))
    logo_canvas.alpha_composite(logo, ((39 - logo.width) // 2, (39 - logo.height) // 2))
    result.alpha_composite(logo_canvas, (22, 20))

    final_path = OUTPUT_DIR / "rabbit-code-reference-final.png"
    result.convert("RGB").save(final_path, optimize=True)
    return final_path


def main():
    cutout, icon_source = make_cutout()
    screen = Image.open(SOURCE_SCREEN)
    final_path = compose(screen, cutout, icon_source)
    print(final_path)


if __name__ == "__main__":
    main()
