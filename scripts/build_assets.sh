#!/usr/bin/env bash
# Régénère le poster affiché en haut du README.
#
#   bash scripts/build_assets.sh
#
# Le poster est la 2e image en data-URI de l'export HTML du design ; ce script
# le ré-extrait puis y repeint les chiffres (54 repos, 10 854 contributions,
# 523 stars) en recyclant les glyphes du poster lui-même — la police du design
# n'existe pas sur la machine, donc repeindre avec une autre se verrait.
#
# Les scripts generate_*.py produisent d'autres SVG (hero, grille, panneaux)
# qui ne sont plus référencés par le README : ils servent à pouvoir retravailler
# le design plus tard.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/repaint_stats.py
echo
ls -l assets/matrix-profile.webp