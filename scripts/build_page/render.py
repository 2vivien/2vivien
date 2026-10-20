"""Rend la page statique puis la découpe en bandes, sans jamais couper un panneau.

  python3 scripts/build_page/render.py

Rendu en 2× (deviceScaleFactor 2) pour que le texte de 8-10 px de la maquette
reste net en retina sur GitHub (contenu ~1010 px CSS, source ~2020 px).

Le fond (texture + pluie) est une seule couche qui couvre tout le document :
les bandes se succèdent donc sans couture visible.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT_DIR = ROOT / "assets"
WORK = Path("/tmp/matrix-build")
SCALE = 2
WIDTH = 1010
HEIGHT = 4200  # borne haute de la capture, largement suffisante


def chrome(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "google-chrome",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--virtual-time-budget=12000",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def read_offsets() -> list[dict]:
    """Récupère la position de chaque bandeau depuis la page rendue."""
    dom = chrome(
        [
            "--dump-dom",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--force-device-scale-factor={SCALE}",
            (HERE / "page.html").as_uri(),
        ]
    ).stdout
    m = re.search(r'<pre id="band-offsets">(.*?)</pre>', dom, re.S)
    if not m:
        raise SystemExit("band-offsets introuvable : la page n'a pas fini de charger.")
    return json.loads(m.group(1))


def render() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "full.png"
    chrome(
        [
            f"--screenshot={out}",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--force-device-scale-factor={SCALE}",
            (HERE / "page.html").as_uri(),
        ]
    )
    return out


def main() -> int:
    offsets = read_offsets()
    full = render()
    img = Image.open(full)
    print(f"page rendue : {img.size[0]}x{img.size[1]}")

    # la hauteur utile s'arrête à la fin de la dernière bande
    bottom = offsets[-1]["top"] + offsets[-1]["height"]
    img = img.crop((0, 0, img.width, min(img.height, bottom * SCALE)))
    img.save(WORK / "full.png")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("section-*.webp"):
        old.unlink()

    prev_end = 0
    for i, band in enumerate(offsets, start=1):
        # on part de la fin du bandeau précédent : les bandes se.tile
        # exactement, même si le navigateur calcule une marge sortante
        top = prev_end * SCALE
        bot = (band["top"] + band["height"]) * SCALE
        prev_end = band["top"] + band["height"]
        crop = img.crop((0, top, img.width, bot))
        name = f"section-{i:02d}-{band['name'].split('-', 1)[-1]}.webp"
        path = OUT_DIR / name
        # WebP lossless : divise le poids par deux par rapport au PNG, sans
        # toucher aux pixels — indispensable ici, le texte fait 8-10 px
        crop.save(path, "WEBP", lossless=True, method=6, quality=100)
        print(f"  {name:44} {crop.width}x{crop.height}  ({crop.width // SCALE}px CSS)")

    print(f"\n{len(offsets)} bandes écrites dans {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
