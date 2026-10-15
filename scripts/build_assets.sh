#!/usr/bin/env bash
# Régénère tous les assets du README.
#
#   bash scripts/build_assets.sh
#
# Le hero SVG reproduit le composant <BinaryFace> de l'export React d'origine.
# Pour recaler la densité et la luminosité du visage sur une capture de
# référence, lance scripts/compare_face.py avec MATRIX_REFERENCE pointant
# vers cette capture (le script sort proprement si le fichier est absent).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/generate_hero.py
python3 scripts/generate_graph.py
python3 scripts/generate_panels.py
echo
ls -l assets/matrix-*.svg