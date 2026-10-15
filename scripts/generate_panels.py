"""Génère les panneaux SVG qui vivent de la couleur.

GitHub supprime tous les attributs `style` inline (vérifié sur le profil :
`<span style="color:...">`, `<font color>`, `!important` — tout est retiré).
Seules les images conservent la couleur, donc les blocs dont le rendu dépend
de la teinte vert Matrix sont pré-rendus ici :

  matrix-stack.svg    grille de chips [TAG] de la tech stack
  matrix-langs.svg    top languages avec barres
  matrix-metrics.svg  system metrics avec barres hachurées
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets"

BG = "#010409"
PANEL_BG = "#0d1117"
BORDER = "#30363d"
INNER = "#21262d"
WHITE = "#f0f6fc"
DIM = "#8b949e"
GREEN = "#39d353"

MONO = "'JetBrains Mono','SFMono-Regular',ui-monospace,Consolas,'Liberation Mono',monospace"

STACK = [
    ("HTML5", "HTML"),
    ("CSS3", "CSS"),
    ("JS", "JavaScript"),
    ("TS", "TypeScript"),
    ("REACT", "React"),
    ("TAIL", "Tailwind"),
    ("NODE", "Node.js"),
    ("EXP", "Express"),
    ("NEST", "NestJS"),
    ("PY", "Python"),
    ("MDB", "MongoDB"),
    ("RD", "Redis"),
    ("PRISMA", "Prisma"),
    ("GIT", "Git"),
    ("FIG", "Figma"),
    ("DOCKER", "Docker"),
    ("LINUX", "Linux"),
    ("VERCEL", "Vercel"),
    ("PYR", "PyTorch"),
    ("OPENAI", "OpenAI"),
    ("GRAPHQL", "GraphQL"),
    ("LANG", "LangChain"),
]

LANGS = [
    ("JavaScript", "", 38),
    ("Python", "", 28),
    ("TypeScript", "", 17),
    ("Rust", "", 9),
    ("Go", "", 5),
    ("Other", "", 3),
]

METRICS = [
    ("Uptime", "99.92%", 99.92),
    ("Avg Commit/Day", "4.7", 46),
    ("CI Pass Rate", "96%", 96),
    ("Coverage", "84%", 84),
]


def panel(width: int, height: int, title: str, body: str) -> str:
    """Cadre commun : bordure, titre `> TITRE`, filet pointillé."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">'
        f'<rect width="{width}" height="{height}" fill="{PANEL_BG}"/>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" fill="none" '
        f'stroke="{BORDER}"/>'
        f'<rect x="1" y="1" width="{width - 2}" height="26" fill="{BG}" fill-opacity="0.7"/>'
        f'<line x1="0" y1="27.5" x2="{width}" y2="27.5" stroke="{BORDER}" '
        'stroke-dasharray="2 3"/>'
        f'<text x="10" y="18" font-family="{MONO}" font-size="10.5" font-weight="700" '
        f'letter-spacing="1.4" fill="{WHITE}">&gt; {title}</text>'
        f"{body}</svg>"
    )


def chip_grid() -> str:
    cols, cw, ch, gap = 4, 78.0, 34.0, 6.0
    pad = 10.0
    width = int(cols * (cw + gap) + gap + 2 * pad)
    rows = -(-len(STACK) // cols)
    height = int(38 + rows * (ch + gap) + gap)

    body = []
    for i, (tag, name) in enumerate(STACK):
        r, c = divmod(i, cols)
        x = pad + gap + c * (cw + gap)
        y = 38 + r * (ch + gap)
        tag_size = 8.5 if len(tag) <= 7 else 7.0
        name_size = 8.0 if len(name) <= 9 else 6.8
        body.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{ch:.1f}" '
            f'fill="{BG}" stroke="{BORDER}"/>'
            # petit carré blanc en haut à droite, comme dans la capture
            f'<rect x="{x + cw - 4:.1f}" y="{y:.1f}" width="4" height="4" fill="{WHITE}"/>'
            f'<text x="{x + 5:.1f}" y="{y + 15:.1f}" font-family="{MONO}" '
            f'font-size="{tag_size}" font-weight="700" fill="{WHITE}">'
            f"[{tag}]</text>"
            f'<text x="{x + 5:.1f}" y="{y + 27:.1f}" font-family="{MONO}" '
            f'font-size="{name_size}" fill="{WHITE}" fill-opacity="0.9">'
            f"{name}</text>"
        )
    return panel(width, height, "TECH STACK", "".join(body))


def bars(
    width: int,
    title: str,
    rows: list[tuple[str, str, int]],
    label_w: float,
    bar_color: str,
    bar_h: float = 8.0,
    row_h: float = 20.0,
    pct_suffix: bool = True,
) -> str:
    pad = 10.0
    height = int(38 + len(rows) * row_h + 8)
    bar_x = pad + label_w + (34 if any(r[1] for r in rows) else 10)
    bar_max = width - bar_x - pad - (30 if pct_suffix else 0)

    body = []
    for i, (label, value, pct) in enumerate(rows):
        y = 40 + i * row_h
        body.append(
            f'<text x="{pad}" y="{y + bar_h:.1f}" font-family="{MONO}" font-size="10" '
            f'fill="{WHITE}">{label}</text>'
        )
        if value:
            body.append(
                f'<text x="{pad + label_w:.1f}" y="{y + bar_h:.1f}" text-anchor="end" '
                f'font-family="{MONO}" font-size="10" font-weight="700" fill="{WHITE}">'
                f"{value}</text>"
            )
        body += [
            # piste, puis hachures, puis le remplissage par-dessus : sinon les
            # hachures ternissent la barre comme dans la capture
            f'<rect x="{bar_x:.1f}" y="{y}" width="{bar_max:.1f}" height="{bar_h:.1f}" '
            f'fill="{INNER}"/>',
            f'<rect x="{bar_x:.1f}" y="{y}" width="{bar_max:.1f}" height="{bar_h:.1f}" '
            'fill="url(#hatch)"/>',
            f'<rect x="{bar_x:.1f}" y="{y}" width="{bar_max * pct / 100:.1f}" '
            f'height="{bar_h:.1f}" fill="{bar_color}"/>',
        ]
        if pct_suffix:
            body.append(
                f'<text x="{bar_x + bar_max + 5:.1f}" y="{y + bar_h:.1f}" '
                f'font-family="{MONO}" font-size="9" fill="{DIM}">{pct}%</text>'
            )
        # hachures, comme la barre "Uptime" de la capture
        body.append(
            f'<rect x="{bar_x:.1f}" y="{y}" width="{bar_max:.1f}" height="{bar_h:.1f}" '
            'fill="url(#hatch-light)"/>'
        )
    defs = (
        "<defs>"
        '<pattern id="hatch" width="7" height="7" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="3.5" height="7" fill="#010409" fill-opacity="0.5"/></pattern>'
        '<pattern id="hatch-light" width="7" height="7" '
        'patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="2" height="7" fill="#010409" fill-opacity="0.28"/></pattern>'
        "</defs>"
    )
    return panel(width, height, title, defs + "".join(body))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "matrix-stack.svg": chip_grid(),
        "matrix-langs.svg": bars(330, "TOP LANGUAGES", LANGS, 84, GREEN),
        "matrix-metrics.svg": bars(
            330, "SYSTEM METRICS", METRICS, 122, WHITE, pct_suffix=False
        ),
    }
    for name, svg in outputs.items():
        path = OUT_DIR / name
        path.write_text(svg, encoding="utf-8")
        print(f"{path} — {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
