"""Compare le profil de luminosité du visage entre le SVG généré et la référence.

Usage : python3 scripts/compare_face.py
Renvoie, par tranche de luminance source, la luminosité moyenne des points
rendus dans le SVG et dans la capture de référence.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_hero import COLS, ROWS, sample_cover  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
HERO = ROOT / "assets" / "matrix-hero.svg"
SRC = Path(os.environ.get("MATRIX_PORTRAIT", ROOT / "assets" / "source-portrait.png"))
# La capture de référence n'est pas versionnée : ce script sert à recalibrer le
# hero, il n'est utile que si on l'a sous la main.
REF = Path(os.environ.get("MATRIX_REFERENCE", "/tmp/matrix-reference.png"))
TMP = Path("/tmp")

# alignement du canvas dans la capture de référence (relevé par recherche)
REF_X0, REF_Y0, REF_CX, REF_CY = 710, 140, 5.4, 4.8


def render_svg() -> np.ndarray:
    out = TMP / "_cmp_render.png"
    subprocess.run(
        [
            "google-chrome",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            f"--screenshot={out}",
            "--window-size=1200,800",
            HERO.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    return np.asarray(Image.open(out).convert("L"), dtype=float)


def profile(
    grid: list[list[float]], img: np.ndarray, x0: int, y0: int, cx: float, cy: float
):
    buckets: dict[int, list[float]] = {}
    for r in range(ROWS):
        for c in range(COLS):
            lum = grid[r][c]
            if lum < 0.05:
                continue
            ys, xs = int(y0 + r * cy), int(x0 + c * cx)
            patch = img[ys : ys + int(cy) + 1, xs : xs + int(cx) + 1]
            if patch.size == 0:
                continue
            buckets.setdefault(min(9, int(lum * 10)), []).append(float(patch.mean()))
    return {b: float(np.mean(v)) for b, v in sorted(buckets.items())}


def main() -> int:
    if not REF.exists():
        print(f"pas de capture de référence ({REF}) — comparaison ignorée.")
        return 0
    grid = sample_cover(Image.open(SRC), COLS, ROWS)
    ref = profile(
        grid,
        np.asarray(Image.open(REF).convert("L"), dtype=float),
        REF_X0,
        REF_Y0,
        REF_CX,
        REF_CY,
    )
    svg = profile(grid, render_svg(), 340, 22, 6.0465, 6.0870)

    print(f"{'luminance':>10} {'ref':>8} {'svg':>8} {'écart':>8}")
    for b in sorted(set(ref) | set(svg)):
        r, s = ref.get(b, 0.0), svg.get(b, 0.0)
        print(f"{b / 10:>10.1f} {r:>8.1f} {s:>8.1f} {s - r:>8.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
