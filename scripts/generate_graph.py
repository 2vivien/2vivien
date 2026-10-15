"""Génère assets/matrix-graph.svg : la grille de contributions façon GitHub.

53 semaines x 7 jours, comme la capture de référence : des carrés empilés dont
la hauteur suit une profil en "colline" (faible en janvier, pic en été, repli
en décembre), avec le nombre de contributions écrit dans chaque case.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "matrix-graph.svg"

WEEKS, DAYS = 53, 7
CELL, GAP = 11.0, 2.0
STEP = CELL + GAP
PAD_X, TOP, LABEL_H = 2.0, 2.0, 16.0

W = WEEKS * STEP
H = DAYS * STEP + TOP + LABEL_H

BG = "#010409"
FG_MUTED = "#484f58"

# palette de contributions, identique au vert GitHub
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
LEVEL_FG = ["#484f58", "#c9d1d9", "#ffffff", "#ffffff", "#ffffff"]

MONO = "'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,monospace"

# mois repères (colonne, libellé) — 7 jours par colonne, dimanche en haut
MONTHS = [(1, "Jan"), (14, "Apr"), (27, "Jul"), (39, "Oct"), (48, "Dec")]


def level(count: int) -> int:
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def activity(week: int, rng: random.Random) -> list[int]:
    """Nombre de contributions par jour : profil en colline + bruit + week-end creux."""
    # pic Eugene autour de la semaine 27 (mi-juillet)
    peak = math.exp(-(((week - 27) / 17.0) ** 2))
    base = 1.2 + 8.0 * peak
    counts = []
    for day in range(DAYS):
        weekend = 0.45 if day >= 5 else 1.0
        value = base * weekend + rng.uniform(-1.6, 2.4)
        counts.append(max(0, int(round(value))))
    return counts


def build() -> str:
    rng = random.Random(2024)
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
        f'viewBox="0 0 {W:.0f} {H:.0f}" role="img" '
        'aria-label="Grille de contributions GitHub 2024">',
        "<title>GitHub contributions 2024</title>",
        f'<rect width="{W:.0f}" height="{H:.0f}" fill="{BG}"/>',
    ]

    for week in range(WEEKS):
        for day, count in enumerate(activity(week, rng)):
            lv = level(count)
            x = PAD_X + week * STEP
            y = TOP + day * STEP
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL:.1f}" height="{CELL:.1f}" '
                f'rx="2" fill="{LEVELS[lv]}"/>'
            )
            if count:
                parts.append(
                    f'<text x="{x + CELL / 2:.1f}" y="{y + CELL / 2 + 3.2:.1f}" '
                    f'text-anchor="middle" font-family="{MONO}" font-size="7" '
                    f'fill="{LEVEL_FG[lv]}">{count}</text>'
                )

    for col, label in MONTHS:
        x = PAD_X + col * STEP
        parts.append(
            f'<text x="{x:.1f}" y="{H - 4:.1f}" font-family="{MONO}" font-size="9" '
            f'fill="{FG_MUTED}">{label}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    svg = build()
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT} — {len(svg) / 1024:.1f} KB")
