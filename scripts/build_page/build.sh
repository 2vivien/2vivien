#!/usr/bin/env bash
# Reconstruit le profil : assets de la page statique puis découpe en bandes.
#
#   bash scripts/build_page/build.sh
#
# Le README est une pile de captures de sections. Pour qu'il n'y ait aucune
# couture visible, la page est rendue en un seul tenant (le fond — grain et
# pluie — est une couche unique qui couvre toute la hauteur) puis découpée
# aux frontières de panneaux. Recollées, les bandes redonnent le rendu
# d'origine au pixel près.
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 scripts/build_page/make_res.py
python3 scripts/build_page/render.py
echo
du -sh assets/
