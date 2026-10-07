#!/usr/bin/env python3
"""Hook PreToolUse (Write) : refuse une fiche de sorties/ qui contient un montant sans source.

Règle : toute ligne contenant un montant en euros doit porter une note de bas de page [^n], et la
fiche doit se terminer par une section « ## Sources ». Code de sortie 2 = écriture bloquée ; le
message sur stderr est renvoyé à Claude, qui corrige la fiche et réessaie.
"""
import json
import re
import sys

MONTANT = re.compile(r"\d[\d\s .,]*\s?(€|euros?\b)", re.IGNORECASE)

evenement = json.load(sys.stdin)
entree = evenement.get("tool_input", {})
chemin = entree.get("file_path", "")
if "/sorties/" not in chemin or not chemin.endswith(".md"):
    sys.exit(0)

texte = entree.get("content", "")
problemes = []
lignes = texte.splitlines()
for num, ligne in enumerate(lignes, 1):
    if ligne.startswith("[^"):  # les définitions de notes ne sont pas concernées
        continue
    if MONTANT.search(ligne) and "[^" not in ligne:
        problemes.append(f"ligne {num} : « {ligne.strip()[:80]} »")
if not any(l.strip().lower().startswith("## sources") for l in lignes):
    problemes.append("section « ## Sources » absente")

if problemes:
    print("Fiche refusée : montant sans source.\n- " + "\n- ".join(problemes)
          + "\nAjoute une note [^n] renvoyant à la source de chaque montant.", file=sys.stderr)
    sys.exit(2)
