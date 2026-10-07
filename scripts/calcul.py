#!/usr/bin/env python3
"""Calcul du budget OPCO annuel d'une entreprise. Partie DÉTERMINISTE : aucune IA ici.

    python3 scripts/calcul.py --entreprise travail/123456789.json --bareme data/baremes/ATLAS-1486-2026.json \
        [--prix 3000] [--heures 25]

Le budget affiché est le plafond de prise en charge de l'entreprise pour l'année (plan de
développement des compétences). Si un prix est fourni, le script calcule aussi la prise en charge
et le reste à charge.
"""
import argparse
import json
from pathlib import Path


def charger(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def regle_pour_segment(bareme, segment):
    """Le barème contient une règle par segment d'effectif ; on prend celle qui correspond."""
    return next((r for r in bareme.get("regles", []) if r.get("segment") == segment), None)


def reste_a_charge(budget, horaire, prix_ht, heures):
    """Si un prix est donné : prise en charge = minimum entre le prix, le budget et le coût horaire max × heures."""
    if prix_ht is None:
        return {}
    plafonds = {"prix de la formation": prix_ht}
    if budget is not None:
        plafonds["budget OPCO"] = budget
    if horaire is not None and heures:
        plafonds["coût horaire max × heures"] = horaire * heures
    limitant = min(plafonds, key=plafonds.get)
    prise = round(plafonds[limitant], 2)
    return {
        "prix_formation_ht": prix_ht,
        "heures": heures,
        "prise_en_charge_estimee_ht": prise,
        "reste_a_charge_ht": round(prix_ht - prise, 2),
        "facteur_limitant": limitant,
    }


def calculer(ent, bareme, prix_ht=None, heures=None):
    segment = ent["effectif"]["segment"]
    alertes = []

    if segment == "50 salariés et plus":
        return {
            "budget_opco_ht": None,
            **({"prix_formation_ht": prix_ht, "prise_en_charge_estimee_ht": 0, "reste_a_charge_ht": prix_ht} if prix_ht is not None else {}),
            "eligible_plan_opco": False,
            "motif": "Au-delà de 49 salariés, l'OPCO ne finance plus le plan de développement des compétences sur les fonds légaux.",
            "pistes": ["Fonds conventionnels ou versements volontaires auprès de l'OPCO", "Pro-A (reconversion ou promotion par alternance)", "Budget formation interne de l'entreprise"],
        }
    if segment == "inconnu" or ent["effectif"]["code"] in ("NN", "00"):
        alertes.append("Effectif nul ou inconnu à l'INSEE : vérifier que l'entreprise a bien des salariés (un dirigeant non salarié relève du FAF de sa profession, pas de l'OPCO).")

    regle = regle_pour_segment(bareme, segment)
    if bareme.get("fonds_epuises"):
        alertes.append("Fonds de la branche signalés comme épuisés ou suspendus par l'OPCO : le budget réellement mobilisable peut être nul, à confirmer auprès de l'OPCO.")
    if regle is None:
        return {"budget_opco_ht": None, "eligible_plan_opco": None, "motif": f"Aucune règle de barème trouvée pour le segment « {segment} ».", "alertes": alertes}

    annuel, par_action, horaire = (regle.get(k) for k in ("plafond_annuel_entreprise_ht", "plafond_par_action_ht", "cout_horaire_max_ht"))
    if annuel is not None:
        budget, base = annuel, "plafond annuel entreprise"
    elif par_action is not None:
        budget, base = par_action, "plafond par action de formation"
        alertes.append("Seul un plafond par action est connu : le budget annuel peut être supérieur si l'entreprise finance plusieurs actions.")
    else:
        budget, base = None, None
        alertes.append("Aucun plafond en euros trouvé : seul le coût horaire maximum est connu.")

    if budget is not None:
        alertes.append("Ce budget est partagé entre toutes les formations de l'entreprise sur l'année : il a peut-être déjà été en partie consommé.")

    return {
        **reste_a_charge(budget, horaire, prix_ht, heures),
        "budget_opco_ht": budget,
        "base_du_budget": base,
        "eligible_plan_opco": True,
        "segment": segment,
        "cout_horaire_max_ht": horaire,
        # Utile pour dimensionner la formation au budget : nombre d'heures finançables au taux maximum
        "heures_financables_max": int(budget // horaire) if budget is not None and horaire else None,
        "salaires_pris_en_charge": regle.get("prise_en_charge_salaires"),
        "conditions": regle.get("conditions", []),
        "alertes": alertes,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--entreprise", required=True, help="JSON produit par scripts/entreprise.py fiche")
    p.add_argument("--bareme", required=True, help="JSON produit par le sous-agent veille-bareme")
    p.add_argument("--prix", type=float, help="prix HT total de la formation (facultatif, pour le reste à charge)")
    p.add_argument("--heures", type=float, help="durée en heures (facultatif, applique le coût horaire max)")
    a = p.parse_args()

    bareme = charger(a.bareme)
    resultat = calculer(charger(a.entreprise), bareme, a.prix, a.heures)
    resultat["bareme"] = {k: bareme.get(k) for k in ("opco", "annee", "date_consultation", "confiance", "sources", "remarques")}
    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
