#!/usr/bin/env bash
# Régénère le hero et la grille, puis affiche le poids des assets.
# Pour recaler la luminosité du visage sur la capture d'origine, lance
# scripts/compare_face.py avec MATRIX_REFERENCE pointant vers cette capture.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/generate_hero.py
python3 scripts/generate_graph.py
ls -l assets/matrix-hero.svg assets/matrix-graph.svg