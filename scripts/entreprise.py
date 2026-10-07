#!/usr/bin/env python3
"""Identification d'une entreprise et de son OPCO à partir de données publiques officielles.

Partie DÉTERMINISTE de l'agent : aucune IA ici, uniquement des API publiques.

    python3 scripts/entreprise.py chercher "Nom de l'entreprise"   -> liste de candidats
    python3 scripts/entreprise.py fiche 123456789                   -> fiche complète + OPCO

Sources :
- API Recherche d'entreprises (DINUM) : https://recherche-entreprises.api.gouv.fr
- Table SIRET-OPCO « SIRO » (France compétences) via l'API tabulaire data.gouv.fr
"""
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

API_ENTREPRISES = "https://recherche-entreprises.api.gouv.fr/search"
SIRO_RESOURCE = "b2452a3d-7786-4a26-99c3-0389fbb3763e"
API_SIRO = f"https://tabular-api.data.gouv.fr/api/resources/{SIRO_RESOURCE}/data/"
PAGE_SIRO = "https://www.data.gouv.fr/datasets/table-siret-opco"

# Tranches d'effectif INSEE : code -> (libellé, borne haute de la tranche)
TRANCHES = {
    "NN": ("non employeuse", 0), "00": ("0 salarié", 0), "01": ("1 ou 2 salariés", 2),
    "02": ("3 à 5 salariés", 5), "03": ("6 à 9 salariés", 9), "11": ("10 à 19 salariés", 19),
    "12": ("20 à 49 salariés", 49), "21": ("50 à 99 salariés", 99), "22": ("100 à 199 salariés", 199),
    "31": ("200 à 249 salariés", 249), "32": ("250 à 499 salariés", 499), "41": ("500 à 999 salariés", 999),
    "42": ("1 000 à 1 999 salariés", 1999), "51": ("2 000 à 4 999 salariés", 4999),
    "52": ("5 000 à 9 999 salariés", 9999), "53": ("10 000 salariés et plus", 10**9),
}


def get_json(url, params):
    full = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(full, headers={"User-Agent": "budget-opco-demo/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r), full
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        # Python macOS sans certificats installés : on passe par curl, présent partout
        out = subprocess.run(["curl", "-sf", "--max-time", "20", full], capture_output=True, text=True, check=True)
        return json.loads(out.stdout), full


def tranche(code):
    libelle, borne = TRANCHES.get(code or "", ("inconnue", None))
    if borne is None:
        segment = "inconnu"
    elif borne < 11:
        segment = "moins de 11 salariés"
    elif borne < 50:
        segment = "11 à 49 salariés"
    else:
        segment = "50 salariés et plus"
    return {"code": code, "libelle": libelle, "segment": segment}


def chercher(nom):
    data, url = get_json(API_ENTREPRISES, {"q": nom, "per_page": 5, "etat_administratif": "A"})
    candidats = [
        {
            "siren": e["siren"],
            "nom": e["nom_complet"],
            "ville": (e.get("siege") or {}).get("libelle_commune"),
            "naf": e.get("activite_principale"),
            "effectif": tranche(e.get("tranche_effectif_salarie"))["libelle"],
            "date_creation": e.get("date_creation"),
        }
        for e in data.get("results", [])
    ]
    return {"requete": nom, "nb_resultats": data.get("total_results", 0), "candidats": candidats, "source": url}


def fiche(siren):
    data, url_ent = get_json(API_ENTREPRISES, {"q": siren, "per_page": 1})
    res = [e for e in data.get("results", []) if e["siren"] == siren]
    if not res:
        return {"erreur": f"SIREN {siren} introuvable", "source": url_ent}
    e = res[0]
    siege = e.get("siege") or {}

    # OPCO : tous les établissements de l'entreprise présents dans la table SIRO
    siro, url_siro = get_json(API_SIRO, {"SIRET__contains": siren, "page_size": 50})
    etabs = [
        {"siret": l["SIRET"], "idcc": l["IDCC"], "opco": l["OPCO_PROPRIETAIRE"], "opco_gestion": l["OPCO_GESTION"]}
        for l in siro.get("data", []) if l["SIRET"].startswith(siren)
    ]
    opcos = sorted({x["opco"] for x in etabs if x["opco"]})
    du_siege = next((x for x in etabs if x["siret"] == siege.get("siret")), None)
    opco = (du_siege or {}).get("opco") or (opcos[0] if len(opcos) == 1 else None)

    eff = tranche(e.get("tranche_effectif_salarie"))
    return {
        "date_extraction": date.today().isoformat(),
        "entreprise": {
            "siren": siren,
            "nom": e["nom_complet"],
            "siret_siege": siege.get("siret"),
            "adresse_siege": siege.get("adresse"),
            "naf": e.get("activite_principale"),
            "categorie": e.get("categorie_entreprise"),
            "date_creation": e.get("date_creation"),
            "etat": "active" if e.get("etat_administratif") == "A" else "fermée",
            "nature_juridique": e.get("nature_juridique"),
            "dirigeants": [
                " ".join(filter(None, [d.get("prenoms"), d.get("nom"), d.get("denomination")])) + (f" ({d['qualite']})" if d.get("qualite") else "")
                for d in e.get("dirigeants", [])[:3]
            ],
        },
        "effectif": {**eff, "annee": e.get("annee_tranche_effectif_salarie")},
        "conventions_collectives_idcc": siege.get("liste_idcc") or sorted({x["idcc"] for x in etabs if x["idcc"]}),
        "opco": {
            "nom": opco,
            "statut": "trouvé" if opco else ("plusieurs OPCO" if len(opcos) > 1 else "non trouvé"),
            "tous": opcos,
            "etablissements": etabs,
        },
        "sources": {
            "entreprise": url_ent,
            "opco": url_siro,
            "opco_page": PAGE_SIRO,
        },
    }


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("chercher", "fiche"):
        sys.exit(__doc__)
    cmd, arg = sys.argv[1], sys.argv[2].strip()
    try:
        out = chercher(arg) if cmd == "chercher" else fiche(arg.replace(" ", "")[:9])
    except Exception as exc:  # réseau, API indisponible…
        out = {"erreur": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(out, ensure_ascii=False, indent=2))
