"""Génère les images de la page statique (scripts/build_page/res/).

  python3 scripts/build_page/make_res.py

Tout est produit en Python plutôt que dans un canvas du navigateur :
en `file://` le canvas se retrouve "tainted" et `getImageData` lève une
SecurityError — le visage binaire restait donc vide. En Python il n'y a pas
d'async ni d'aléatoire non maîtrisé : le rendu est identique à chaque run.

Toutes les images sont produites en 2× de leur taille d'affichage, la page
étant rendue en deviceScaleFactor 2 (net en retina sur GitHub).
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RES = HERE / "res"
PORTRAIT = RES / "portrait.jpg"
FONT_PATH = RES / "fonts" / "JetBrainsMono.ttf"

# --- visage binaire ---------------------------------------------------------
COLS, ROWS = 86, 92
FACE_W, FACE_H = 1000, 1076  # 2× de 500x538
SS = 3  # suréchantillonnage pour l'anticrénelage

# Algorithme du composant <BinaryFace> de l'export React :
#   alpha = luminance^1.2 * 0.95 + 0.04, blanc au-dessus de 0.5 de luminance.
# On relève légèrement la courbe : avec la formule d'origine le visage
# disparaissait dans le fond — c'était le défaut le plus visible sur les
# captures d'écran de l'export.
ALPHA_GAIN, ALPHA_GAMMA = 1.8, 0.9
GLYPH_SCALE = 1.1  # le dessin d'origine tombait trop fin pour rester lisible


def build_face() -> Image.Image:
    src = Image.open(PORTRAIT).convert("RGB")
    # même cadrage que le drawImage de l'export React : cover + décalage -6
    scale = max(COLS / src.width, ROWS / src.height)
    dw, dh = round(src.width * scale), round(src.height * scale)
    dx, dy = round((COLS - dw) / 2) - 6, round((ROWS - dh) / 2) - 6
    off = Image.new("RGB", (COLS, ROWS), (0, 0, 0))
    off.paste(src.resize((dw, dh), Image.LANCZOS), (dx, dy))
    px = off.load()

    w, h = FACE_W * SS, FACE_H * SS
    big = Image.new("RGBA", (w, h), (1, 4, 9, 255))
    draw = ImageDraw.Draw(big)
    rnd = random.Random(4242)
    cell_x, cell_y = w / COLS, h / ROWS
    font = ImageFont.truetype(FONT_PATH, max(6, round(cell_y * 0.9 * GLYPH_SCALE)))

    for y in range(ROWS):
        for x in range(COLS):
            r, g, b = px[x, y]
            lum = (r * 0.3 + g * 0.59 + b * 0.11) / 255
            alpha = min(1.0, ALPHA_GAIN * lum**ALPHA_GAMMA)
            if alpha < 0.08:
                continue
            ch = "1" if rnd.random() > 0.5 else "0"
            colour = (255, 255, 255) if lum > 0.5 else (139, 148, 158)
            draw.text(
                (x * cell_x + cell_x * 0.1, y * cell_y + cell_y * 0.85),
                ch,
                font=font,
                fill=colour + (int(alpha * 255),),
                anchor="ls",
            )
    return big.convert("RGB").resize((FACE_W, FACE_H), Image.LANCZOS)


def build_avatar() -> Image.Image:
    """Avatar 48x48 CSS (96x96 source) : recadrage carré, niveaux de gris."""
    src = Image.open(PORTRAIT).convert("L")
    side = min(src.width, src.height)
    left = (src.width - side) // 2
    top = int((src.height - side) * 0.18)  # visage un peu plus haut que le centre
    im = src.crop((left, top, left + side, top + side)).resize((96, 96), Image.LANCZOS)
    # étirement de contraste, comme le `contrast-125` de l'export
    lut = [
        min(255, max(0, int((v / 255 - 0.5) * 1.55 * 255 + 128))) for v in range(256)
    ]
    return im.point(lut).convert("RGB")


def build_graph() -> Image.Image:
    """Grille de contributions 53x7.

    La hauteur suit exactement les 7 rangées : une image plus haute
    laisserait un bandeau vide sous la grille, visible dans le panneau.
    """
    weeks, days = 53, 7
    w = 400  # 2× de 200 px CSS
    step = w / weeks
    cell = step * 0.82
    h = round(days * step)
    levels = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    img = Image.new("RGB", (w, h), (1, 4, 9))
    draw = ImageDraw.Draw(img)
    rnd = random.Random(2024)
    for wk in range(weeks):
        peak = math.exp(-(((wk - 27) / 17.0) ** 2))
        base = 1.2 + 8.0 * peak
        for d in range(days):
            weekend = 0.45 if d >= 5 else 1.0
            n = max(0, int(round(base * weekend + (rnd.random() * 4 - 1.6))))
            lv = 0 if n == 0 else 1 if n <= 2 else 2 if n <= 5 else 3 if n <= 9 else 4
            x0, y0 = wk * step, d * step
            draw.rectangle([x0, y0, x0 + cell, y0 + cell], fill=levels[lv])
    return img


def build_noise() -> Image.Image:
    """Grain 256x256 répété, pour la texture de fond.

    L'export React utilisait le poster lui-même en fond à 2,5 % : étiré sur
    toute la hauteur, le texte du poster devenait lisible en arrière-plan et
    parasitait la lecture. Un vrai grain évite ça.
    """
    size = 256
    img = Image.new("RGBA", (size, size))
    px = img.load()
    rnd = random.Random(7)
    for y in range(size):
        for x in range(size):
            px[x, y] = (240, 246, 252, rnd.randint(0, 14))
    return img


def main() -> None:
    RES.mkdir(parents=True, exist_ok=True)
    for name, fn in (
        ("face.png", build_face),
        ("avatar.png", build_avatar),
        ("graph.png", build_graph),
        ("noise.png", build_noise),
    ):
        img = fn()
        path = RES / name
        img.save(path, optimize=True)
        print(
            f"{path.name:14} {img.size[0]}x{img.size[1]}  {path.stat().st_size // 1024} KB"
        )


if __name__ == "__main__":
    main()
