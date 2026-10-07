#!/usr/bin/env python3
"""Regroupe data/baremes/*.json dans web/baremes.json pour l'interface web.

Les barèmes n'ont qu'une source : data/baremes/, alimenté par le sous-agent veille-bareme.
Lancé par Netlify à chaque déploiement (voir netlify.toml), ou à la main :

    python3 scripts/exporter_baremes.py
"""
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
baremes = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((RACINE / "data" / "baremes").glob("*.json"))]
sortie = RACINE / "web" / "baremes.json"
sortie.write_text(json.dumps(baremes, ensure_ascii=False), encoding="utf-8")
print(f"{len(baremes)} barème(s) exporté(s) vers {sortie.relative_to(RACINE)} : "
      + ", ".join(f"{b['opco']} IDCC {b.get('idcc')} {b['annee']}" for b in baremes))
