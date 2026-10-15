"""Génère assets/matrix-hero.svg : reproduction statique du hero du profil Matrix.

Deux parties :
  1. le visage binaire — même algorithme que le composant <BinaryFace> de l'export
     React : échantillonnage 86x92 en "cover", luminance (0.3R+0.59G+0.11B),
     un caractère "0"/"1" par pixel, blanc si luminance > 0.5 sinon #8b949e,
     opacité = luminance^1.2 * 0.95 + 0.04 (ignoré sous 0.06).
  2. le titre "CODE IS MATRIX" en police pixel 5x7 dessinée en <rect>, donc
     identique partout sans dépendre d'une webfont.

La pluie de 0/1 est tirée une fois (seed fixe) pour garder le SVG déterministe.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(os.environ.get("MATRIX_PORTRAIT", ROOT / "assets" / "source-portrait.png"))
OUT = ROOT / "assets" / "matrix-hero.svg"

# --- géométrie -------------------------------------------------------------
COLS, ROWS = 86, 92
CELL_X, CELL_Y = 6.046511627906977, 6.086956521739131
FACE_W, FACE_H = COLS * CELL_X, ROWS * CELL_Y  # 520 x 560

W, H = 1200, 800
FACE_TOP = 22

# --- reglages du visage, calibres sur la capture de reference --------------
# La densite et la luminosite des points 0/1 ont ete mesurees puis reglees
# pour que la moyenne / p90 / p99 du rendu SVG collent a ceux de la reference.
ALPHA_GAIN = 1.90
ALPHA_GAMMA = 1.00
ALPHA_CUTOFF = 0.08
MICRO_W, MICRO_H = 3, 4
MICRO_PAD = 0.2  # espace entre points ; 0.2 = quasi jointifs comme la référence
DOT_FILL = 1.0
MICRO = {
    "0": (".X.", "X.X", "X.X", ".X."),
    "1": (".X.", "XX.", ".X.", "XXX"),
}
BG = "#010409"
FG_WHITE = "#f0f6fc"
FG_DIM = "#8b949e"
FG_BORDER = "#21262d"

MONO = "'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,monospace"

# --- police pixel 5x7 (aucune dépendance externe) --------------------------
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def sample_cover(img: Image.Image, cols: int, rows: int) -> list[list[float]]:
    """Reproduit le ctx.drawImage du composant React (offsets négatifs inclus).

    Le canvas d'origine fait :
        scale = max(cols / iw, rows / ih)
        drawImage(img, (cols - iw * scale) / 2, (rows - ih * scale) / 2 - 6, ...)
    ce qui déborde du canvas et décale le cadrage. On rejoue la sémantique
    exacte : on redimensionne puis on colle sur un canvas noir en (cols, rows).
    """
    scale = max(cols / img.width, rows / img.height)
    dw, dh = round(img.width * scale), round(img.height * scale)
    dx = round((cols - dw) / 2) - 6
    dy = round((rows - dh) / 2) - 6
    canvas = Image.new("RGB", (cols, rows), (0, 0, 0))
    canvas.paste(img.convert("RGB").resize((dw, dh), Image.LANCZOS), (dx, dy))
    px = canvas.load()
    return [
        [
            (r * 0.3 + g * 0.59 + b * 0.11) / 255
            for r, g, b in (px[x, y] for x in range(cols))
        ]
        for y in range(rows)
    ]


def micro_font() -> str:
    """Symboles <g> des chiffres 0/1, dessines en rects.

    On evite le texte SVG : a cette taille (cellule de 6 px) une webfont donne
    des jambages si fins qu'ils disparaissent au raster, alors que des rects
    plein sont rendus de facon fiable et identique sur GitHub comme en local.
    """
    ux = CELL_X / (MICRO_W + MICRO_PAD)
    uy = CELL_Y / (MICRO_H + MICRO_PAD)
    out: list[str] = []
    for name, rows in MICRO.items():
        rects = "".join(
            f'<rect x="{c * ux:.2f}" y="{r * uy:.2f}" '
            f'width="{ux * DOT_FILL:.2f}" height="{uy * DOT_FILL:.2f}" '
            f'rx="{uy * 0.18:.2f}"/>'
            for r, row in enumerate(rows)
            for c, cell in enumerate(row)
            if cell == "X"
        )
        out.append(f'<g id="d{name[0]}">{rects}</g>')
    return "".join(out)


def face(rng: random.Random) -> str:
    grid = sample_cover(Image.open(SRC), COLS, ROWS)
    out = [f'<g transform="translate({(W - FACE_W) / 2:.2f},{FACE_TOP})">']
    for y in range(ROWS):
        for x in range(COLS):
            lum = grid[y][x]
            alpha = min(1.0, ALPHA_GAIN * lum**ALPHA_GAMMA)
            if alpha < ALPHA_CUTOFF:
                continue
            glyph = "d1" if rng.random() > 0.5 else "d0"
            fill = FG_WHITE if lum > 0.5 else FG_DIM
            out.append(
                f'<use href="#{glyph}" x="{x * CELL_X:.2f}" y="{y * CELL_Y:.2f}" '
                f'fill="{fill}" fill-opacity="{alpha:.3f}"/>'
            )
    out.append("</g>")
    return "".join(out)


def rain(rng: random.Random, bottom: float) -> str:
    """Colonnes de 0/1 en fond.

    La pluie est estompee au-dessus du visage : sans ça elle noie les traits
    et le rendu ne ressemble plus a la capture de reference.
    """
    out: list[str] = []
    col_w, font, gap = 14.0, 11.0, 17.0
    cy = FACE_TOP + FACE_H * 0.42
    for i in range(int(W / col_w) + 1):
        x = i * col_w + col_w / 2
        y = rng.uniform(-260, FACE_TOP + 420)
        while y < bottom:
            # masque elliptique : la pluie s'efface au-dessus du visage sans
            # laisser de bord rectangulaire
            dx = (x - W / 2) / (FACE_W / 2)
            dy = (y - cy) / (FACE_H * 0.62)
            fade = min(1.0, max(0.0, ((dx * dx + dy * dy) ** 0.5 - 0.78) / 0.34))
            if fade > 0.02:
                out.append(
                    f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" '
                    f'font-size="{font}" fill="{FG_WHITE}" '
                    f'fill-opacity="{rng.uniform(0.05, 0.30) * fade:.3f}" '
                    f'xml:space="preserve">{rng.choice("01")}</text>'
                )
            y += font + gap
    return "".join(out)


def title(text: str, cx: float, top: float, target_w: float) -> tuple[str, float]:
    """Titre en pixel 5x7. Retourne (rects SVG, hauteur totale)."""
    scale = target_w / (len(text) * 6 - 1)
    dot = scale  # un pixel LED = un carré
    pad = scale * 0.14  # espace entre deux points
    unit = dot + pad
    grid_w = (len(text) * 6 - 1) * unit
    x0 = cx - grid_w / 2

    rects: list[str] = []
    for i, ch in enumerate(text):
        glyph = GLYPHS[ch]
        for r, row in enumerate(glyph):
            for c, cell in enumerate(row):
                if cell != "#":
                    continue
                x = x0 + i * 6 * unit + c * unit
                y = top + r * unit
                rects.append(
                    f'<rect x="{x:.2f}" y="{y:.2f}" width="{dot:.2f}" '
                    f'height="{dot:.2f}" rx="{dot * 0.28:.2f}"/>'
                )
    height = 7 * unit
    core = "".join(rects)
    glow = (
        f'<g filter="url(#led-glow)" fill="{FG_WHITE}" fill-opacity="0.5">{core}</g>'
        f'<g filter="url(#led-far)" fill="{FG_WHITE}" fill-opacity="0.28">{core}</g>'
        f'<g fill="{FG_WHITE}">{core}</g>'
    )
    return glow, height


def corner(x: float, y: float, sx: int, sy: int, size: float = 28) -> str:
    return (
        f'<path d="M{x + sx * size},{y} L{x},{y} L{x},{y + sy * size}" fill="none" '
        f'stroke="{FG_WHITE}" stroke-opacity="0.7" stroke-width="1"/>'
    )


def build() -> str:
    rng = random.Random(1337)
    face_bottom = FACE_TOP + FACE_H

    # barre de statut sous le module visage
    bar_y = face_bottom + 16
    title_top = bar_y + 44
    led, led_h = title("CODE IS MATRIX", W / 2, title_top, 620)
    sub_y = title_top + led_h + 34

    parts: list[str] = [
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        "<defs>",
        '<filter id="led-glow" x="-25%" y="-60%" width="150%" height="220%">'
        '<feGaussianBlur stdDeviation="1.6"/></filter>',
        '<filter id="led-far" x="-25%" y="-60%" width="150%" height="220%">'
        '<feGaussianBlur stdDeviation="5"/></filter>',
        '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="2" fill="#ffffff" fill-opacity="0.028"/></pattern>',
        micro_font(),
        "</defs>",
        rain(rng, bar_y - 6),
        face(rng),
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" '
        f'stroke="{FG_BORDER}"/>',
        "".join(
            corner(x, y, sx, sy)
            for x, y, sx, sy in (
                (0, 0, 1, 1),
                (W, 0, -1, 1),
                (0, H, 1, -1),
                (W, H, -1, -1),
            )
        ),
    ]

    # HUD façon terminal
    parts += [
        f'<text x="20" y="200" font-family="{MONO}" font-size="8" fill="{FG_WHITE}" '
        'fill-opacity="0.38">┤ SCAN_Y: 0.42</text>',
        f'<rect x="20" y="208" width="48" height="1" fill="{FG_WHITE}" fill-opacity="0.18"/>',
        f'<text x="20" y="222" font-family="{MONO}" font-size="8" fill="{FG_WHITE}" '
        'fill-opacity="0.38">FACE_MAP: 87%</text>',
        f'<text x="{W - 20}" y="250" text-anchor="end" font-family="{MONO}" font-size="8" '
        f'fill="{FG_WHITE}" fill-opacity="0.38">BINARY_DENSITY: HIGH ┤</text>',
        f'<rect x="{W - 68}" y="258" width="48" height="1" fill="{FG_WHITE}" fill-opacity="0.18"/>',
    ]

    # barre de statut
    parts += [
        f'<rect x="0" y="{bar_y}" width="{W}" height="1" fill="{FG_BORDER}"/>',
        f'<text x="20" y="{bar_y + 22}" font-family="{MONO}" font-size="9" fill="{FG_DIM}">'
        "▶ RENDER_MODE: BINARY_FACE // RES: 86x92 // FPS: 60</text>",
        f'<text x="{W - 20}" y="{bar_y + 22}" text-anchor="end" font-family="{MONO}" '
        f'font-size="9" fill="{FG_DIM}">01010101 11001100 // DECODE</text>',
        led,
        f'<rect x="{W / 2 - 340}" y="{sub_y - 24}" width="680" height="1" '
        'fill="#ffffff" fill-opacity="0.22"/>',
        f'<text x="{W / 2}" y="{sub_y}" text-anchor="middle" font-family="{MONO}" '
        'font-size="13" fill="#ffffff" fill-opacity="0.88">'
        "Fullstack Architect &amp; AI Builder • Building Scalable Systems • "
        "Clean Code • Open Source • AI Integration • Always Learning</text>",
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="url(#scan)"/>',
    ]

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Vivien A. — CODE IS MATRIX">'
        "<title>CODE IS MATRIX</title>" + "".join(parts) + "</svg>"
    )


if __name__ == "__main__":
    if not SRC.exists():
        raise SystemExit(
            f"photo introuvable : {SRC}\n"
            "dépose-la dans assets/source-portrait.png ou renseigne MATRIX_PORTRAIT."
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    svg = build()
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT} — {len(svg) / 1024:.1f} KB")
