from PIL import Image, ImageOps, ImageEnhance

import os
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pfp.png")
RAMP = " .,:;|(){}%#@$"

def render_color(width, char_aspect=0.58, crop=None, contrast=2.2, gamma=0.9,
                 quant=24, min_lum=0.35):
    img = Image.open(SRC).convert("RGB")
    if crop:
        w, h = img.size
        l, t, r, b = crop
        img = img.crop((int(l*w), int(t*h), int(r*w), int(b*h)))
    w, h = img.size
    rows = max(1, int(width * (h / w) * char_aspect))
    color_img = img.resize((width, rows))
    gray = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(contrast)
    gray = gray.resize((width, rows))
    gpx, cpx = gray.load(), color_img.load()

    grid = []
    for y in range(rows):
        row = []
        for x in range(width):
            v = (gpx[x, y] / 255.0) ** gamma
            ch = RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
            r, g, b = cpx[x, y]
            # lift dark colors so they stay visible on the dark card
            lum = (0.299*r + 0.587*g + 0.114*b) / 255.0
            if lum < min_lum and lum > 0:
                k = min_lum / max(lum, 0.02)
                r, g, b = (min(255, int(c * k)) for c in (r, g, b))
            # quantize so adjacent cells merge into runs
            r, g, b = (min(255, (c // quant) * quant + quant // 2) for c in (r, g, b))
            row.append((ch, (r, g, b)))
        grid.append(row)
    return grid

def runs(row):
    out = []
    for ch, col in row:
        if out and (out[-1][1] == col or ch == " "):
            out[-1][0] += ch
        else:
            out.append([ch, col])
    return [(t, c) for t, c in out]
