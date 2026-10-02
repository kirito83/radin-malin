#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Visuels Pinterest 1000x1500 par article (titre + badge categorie)."""
import os

W, H = 1000, 1500

def _font(size, bold=True):
    from PIL import ImageFont
    cands = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()

def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def make_pin(title, category, site_name, out_path):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H))
    top, bot = (13, 17, 32), (38, 48, 92)
    # degrade vertical par bandes
    draw = ImageDraw.Draw(img)
    for y in range(0, H, 4):
        r = y / H
        c = tuple(int(top[i] + (bot[i] - top[i]) * r) for i in range(3))
        draw.rectangle([0, y, W, y + 4], fill=c)
    # pastille categorie
    fb = _font(44)
    cat = category.upper()
    cw = draw.textlength(cat, font=fb) + 70
    draw.rounded_rectangle([ (W - cw) / 2, 120, (W + cw) / 2, 200], radius=40, fill=(255, 214, 10))
    draw.text((W / 2, 160), cat, font=fb, fill=(17, 17, 17), anchor="mm")
    # titre
    ft = _font(72)
    lines = _wrap(draw, title, ft, W - 140)[:7]
    y = 420
    for ln in lines:
        draw.text((W / 2, y), ln, font=ft, fill=(255, 255, 255), anchor="ma")
        y += 100
    # separateur + sous-titre
    draw.rectangle([W / 2 - 120, y + 10, W / 2 + 120, y + 18], fill=(255, 214, 10))
    fs = _font(46, bold=False)
    draw.text((W / 2, y + 90), "TOP 3  •  PRIX VERIFIES", font=fs, fill=(195, 203, 221), anchor="ma")
    # bandeau bas
    draw.rectangle([0, H - 260, W, H], fill=(255, 214, 10))
    fl = _font(64)
    draw.text((W / 2, H - 160), "💰 " + site_name.upper(), font=fl, fill=(17, 17, 17), anchor="mm")
    f2 = _font(36, bold=False)
    draw.text((W / 2, H - 80), "outils gratuits & comparatifs", font=f2, fill=(60, 60, 60), anchor="mm")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, optimize=True)

def build_all(articles, site_name, pins_dir):
    n = 0
    for a in articles:
        out = os.path.join(pins_dir, a["slug"] + ".png")
        if os.path.exists(out):
            continue
        make_pin(a["title"], a["category"], site_name, out)
        n += 1
    return n

if __name__ == "__main__":
    import json
    here = os.path.dirname(os.path.abspath(__file__))
    kws = {k["slug"]: k for k in json.load(open(os.path.join(here, "data", "keywords.json"), encoding="utf-8"))}
    pub = json.load(open(os.path.join(here, "data", "published.json"), encoding="utf-8"))
    slugs = list(pub.keys()) if isinstance(pub, dict) else pub
    arts = [kws[s] for s in slugs if s in kws]
    print(build_all(arts, "Radin Malin", os.path.join(here, "public", "pins")), "visuels")
