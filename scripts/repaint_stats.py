"""Repaint les chiffres du poster CODE IS MATRIX sans changer de police.

Le design est un raster : le seul moyen d'y graver de nouveaux chiffres sans
que la différence se voie est de **recycler les glyphes du poster lui-même**.
La police n'existe pas sur la machine (le meilleur candidat local, Urbanist
SemiBold, ne plafonne qu'à 0.40 d'IoU face à l'original), donc chaque chiffre
est découpé dans le poster puis recomposé : fonte, graisse, anticrénelage et
couleur sont identiques par construction.

Deux lignes de stats, deux tailles de glyphes (13 px et 14 px d'encre) : on
prend donc chaque chiffre sur sa propre ligne quand c'est possible, et les
boîtes sont alignées sur la **ligne de base** et non sur le haut — la virgule
descend sous la base, la-cutting par le haut la transformait en point.

Ordre important : tous les glyphes sont extraits AVANT toute suppression, sinon
on détruirait la source d'un chiffre encore nécessaire.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
# Le poster est la 2e image en data-URI de l'export HTML du design (variable
# `Ua` côté bundle). On la ré-extrait à chaque exécution : sans ça le script
# n'est pas re-exécutable, puisque la source des glyphes est précisément ce
# qu'il remplace.
HTML = ROOT / "Github-Matrix-Profile-Live (1).html"
SRC = ROOT / "assets" / "matrix-profile.webp"
OUT = ROOT / "assets" / "matrix-profile.webp"

# --- lignes de référence ----------------------------------------------------
STATS_BASE = 1044  # ligne "Public Repos: 48 • ... Stars Earned: 312 • ..."
CONTRIB_BASE = 864  # ligne "Contributions: 2,184 Contributions (2024)"
RAIL_BASE = 167  # ligne "Repositories • 48" du rail de droite

# --- bibliothèque de glyphes ------------------------------------------------
# caractère -> (x, y_haut, largeur, hauteur, ligne de base)
# positions relevées sur le profil d'encre colonne par colonne
LIB: dict[str, tuple[int, int, int, int, int]] = {
    # ligne stats (13 px)
    "2": (494, 1032, 10, 13, STATS_BASE),
    "3": (477, 1032, 9, 13, STATS_BASE),
    "4": (255, 1032, 9, 13, STATS_BASE),
    "5": (567, 1032, 9, 13, STATS_BASE),
    # ligne contributions (14 px)
    "0": (441, 851, 10, 14, CONTRIB_BASE),
    "1": (288, 851, 7, 14, CONTRIB_BASE),
    "8": (295, 851, 10, 14, CONTRIB_BASE),
    "4c": (305, 851, 10, 14, CONTRIB_BASE),
    ",": (280, 862, 3, 6, CONTRIB_BASE),
    # rail de droite — le 5 vient de la ligne "Projects • 5", plus bas
    "5r": (1722, 180, 9, 15, RAIL_BASE + 27),
    "4r": (1711, 154, 11, 14, RAIL_BASE),
}

# (plage à effacer, glyphes à composer, décalage initial, ligne de base, fond)
EDITS: list[tuple[tuple[int, int, int, int], list[str], int, int, str]] = [
    # "Public Repos: 48" -> 54
    ((254, 1027, 275, 1050), ["5", "4"], 1, STATS_BASE, "stats"),
    # "Stars Earned: 312" -> 523
    ((476, 1027, 508, 1050), ["5", "2", "3"], 1, STATS_BASE, "stats"),
    # "2,184 Contributions (2024)" -> "10,854"
    # borne basse 870 : les parenthèses descendent jusqu'à y=869 et le pic du
    # graphe de contributions démarre à y=870 — plus bas, on le rase.
    ((267, 846, 480, 870), ["1", "0", ",", "8", "5", "4c"], 4, CONTRIB_BASE, "contrib"),
    # "Repositories • 48" -> 54, aligné à droite sur le même bord
    ((1709, 152, 1733, 170), ["5r", "4r"], 2, RAIL_BASE, "rail"),
]

# suppressions pures : le suffixe " 2024" du titre est devenu faux
ERASES: list[tuple[tuple[int, int, int, int], str, str]] = [
    ((352, 815, 419, 841), "GITHUB STATS 2024", "title"),
]

# échantillonnage du fond, hors du texte
BG_PROBE = {
    "stats": (245, 1026, 640, 1030),
    "contrib": (240, 845, 600, 849),
    "rail": (1600, 149, 1690, 152),
    "title": (180, 814, 340, 817),
}


def extract(img: Image.Image) -> dict[str, Image.Image]:
    out = {}
    for ch, (x, y, w, h, _base) in LIB.items():
        out[ch] = img.crop((x, y, x + w, y + h))
    return out


def median_colour(
    img: Image.Image, box: tuple[int, int, int, int]
) -> tuple[int, int, int]:
    x0, y0, x1, y1 = box
    px = (
        list(img.crop((x0, y0, x1, y1)).get_flattened_data())
        if hasattr(img.crop((x0, y0, x1, y1)), "get_flattened_data")
        else list(img.crop((x0, y0, x1, y1)).getdata())
    )
    return tuple(sorted(p[i] for p in px)[len(px) // 2] for i in range(3))


def gradient_fill(
    img: Image.Image,
    box: tuple[int, int, int, int],
    left_x: int,
    right_x: int,
) -> None:
    """Remplit `box` par interpolation entre deux échantillons hors du cadre.

    Le rail de droite a un halo localisé autour du `•` : un aplat y laisse un
    rectangle gris visible. On relève le fond de part et d'autre du cadre, sur
    chaque ligne, et on interpole.
    """
    x0, y0, x1, y1 = box
    width = max(1, x1 - x0 - 1)
    for y in range(y0, y1):
        left = img.crop((left_x, y, left_x + 3, y + 1)).getpixel((1, 0))
        right = img.crop((right_x, y, right_x + 3, y + 1)).getpixel((1, 0))
        for i, x in enumerate(range(x0, x1)):
            t = i / width
            img.putpixel(
                (x, y),
                tuple(int(round(left[k] + (right[k] - left[k]) * t)) for k in range(3)),
            )


def load_source() -> Image.Image:
    """Récupère le poster d'origine, extrait de l'export HTML commité."""
    if HTML.exists():
        html = HTML.read_text(encoding="utf-8", errors="ignore")
        embedded = re.findall(r"data:image/webp;base64,([A-Za-z0-9+/=]+)", html)
        if len(embedded) >= 2:
            import io

            return Image.open(io.BytesIO(base64.b64decode(embedded[1]))).convert("RGB")
        raise SystemExit(f"{HTML.name} : 2e image data-URI introuvable.")
    raise SystemExit(
        f"{HTML} introuvable — le poster ne peut pas être régénéré.\n"
        "Restaure l'export HTML du design à la racine du dépôt."
    )


def main() -> None:
    img = load_source()
    glyphs = extract(img)  # tout est extrait avant de toucher l'image
    bgs = {k: median_colour(img, v) for k, v in BG_PROBE.items()}
    print("fonds :", bgs)

    for box, keys, offset, base, bg_key in EDITS:
        if bg_key == "rail":
            gradient_fill(img, box, 1705, 1733)
        else:
            img.paste(bgs[bg_key], box)
        x0, _y0, x1, _y1 = box
        pen = x0 + offset
        for key in keys:
            g = glyphs[key]
            _x, _y, _w, h, _src_base = LIB[key]
            # la virgule est plus haute que la base : on colle par le bas
            img.paste(g, (pen, base + 3 - h))
            pen += g.width + 1
        print(f"  {''.join(keys):<8} -> x {x0}..{pen}  (cadre effacé {x0}..{x1})")

    for box, label, bg_key in ERASES:
        img.paste(bgs[bg_key], box)
        print(f"  {label} -> suffixe effacé (x {box[0]}..{box[2]})")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "assets" / "matrix-profile.repaint.png"
    img.save(tmp, "PNG")
    img.save(OUT, "WEBP", quality=95, method=6)
    tmp.unlink()
    print(f"écrit : {OUT}")


if __name__ == "__main__":
    main()
