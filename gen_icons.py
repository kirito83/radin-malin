#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genere les icones du site (logo piece R) dans static/. A relancer si rebranding."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

def font(size):
    for p in ["C:/Windows/Fonts/arialbd.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def base(size=512):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top, bot = (21, 27, 49), (60, 70, 130)
    # fond arrondi degrade
    for y in range(size):
        r = y / size
        c = tuple(int(top[i] + (bot[i] - top[i]) * r) for i in range(3)) + (255,)
        d.line([0, y, size, y], fill=c)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=size // 5, fill=255)
    # piece jaune
    cx = cy = size // 2
    cr = int(size * 0.30)
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(255, 214, 10))
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=(200, 160, 0), width=max(2, size // 128))
    # lettre R
    f = font(int(size * 0.34))
    d.text((cx, cy), "R", font=f, fill=(17, 17, 17), anchor="mm")
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out

def main():
    os.makedirs(STATIC, exist_ok=True)
    big = base(512)
    big.save(os.path.join(STATIC, "icon-512.png"))
    big.resize((192, 192), Image.LANCZOS).save(os.path.join(STATIC, "icon-192.png"))
    big.resize((180, 180), Image.LANCZOS).save(os.path.join(STATIC, "apple-touch-icon.png"))
    big.resize((32, 32), Image.LANCZOS).save(os.path.join(STATIC, "icon-32.png"))
    print("icones OK : 512, 192, 180, 32")

if __name__ == "__main__":
    main()
