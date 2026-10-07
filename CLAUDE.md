# Budget OPCO — agent de Cizel

Outil commercial de Cizel (formation IA pour les TPE/PME). À partir du nom d'une entreprise, il
estime le **budget OPCO** qu'elle peut mobiliser cette année pour former ses salariés. La formation
(durée, contenu, organisme partenaire certifié Qualiopi) s'ajuste ensuite à ce budget.
Point d'entrée : `/budget-opco "<entreprise>"`.

## Répartition du travail
| Brique | Rôle | Pourquoi |
|---|---|---|
| `scripts/entreprise.py` | Nom → SIREN → effectif, IDCC, **OPCO officiel** | Données publiques : un script est exact, un LLM pourrait se tromper |
| sous-agent `veille-bareme` | Recherche web des critères de l'OPCO pour l'année | Pages hétérogènes, à interpréter ; contexte isolé pour ne pas polluer la conversation |
| `scripts/calcul.py` | Barème + effectif → budget OPCO | L'arithmétique ne se confie jamais au LLM |
| hook `verifier_sources.py` | Bloque une fiche contenant un montant sans source | Garde-fou automatique plutôt qu'une consigne qu'on espère suivie |

## Règles
- Afficher le budget OPCO. Le reste à charge n'apparaît que si un prix a été fourni : ne jamais inventer de prix.
- Ne jamais inventer ni recalculer un montant : il vient de `calcul.py`, qui lit un barème sourcé.
- Toujours présenter le résultat comme une **estimation** datée. La décision appartient à l'OPCO.
- L'OPCO vient de la table officielle SIRO, jamais d'une déduction à partir du code NAF.
- À partir de 50 salariés, ne pas promettre de financement OPCO : présenter les pistes alternatives
  renvoyées par `calcul.py`.
- Les fichiers intermédiaires vont dans `travail/`, les fiches finales dans `sorties/`.

## Gabarit de la fiche (`sorties/fiche-*.md`)
Chaque ligne contenant un montant en € doit porter une note de bas de page `[^n]` : le hook le vérifie.

```markdown
# Budget OPCO — {Nom de l'entreprise}
*Estimation du {date} · confiance du barème : {confiance}*

## Budget OPCO estimé : **{budget} € HT / an** [^2]
Base : {base_du_budget} · Coût horaire max : {cout_horaire_max_ht ou « non publié »} [^2]
(si connus : environ {heures_financables_max} h finançables au taux maximum)

(section uniquement si un prix a été fourni)
| | Montant HT |
|---|---|
| Prix de la formation | {prix} € [^3] |
| Prise en charge OPCO estimée | {prise_en_charge} € [^2] |
| **Reste à charge** | **{reste} €** [^2] |
Facteur limitant : {facteur_limitant}

## L'entreprise
SIREN, effectif (tranche + année INSEE), convention collective (IDCC), **OPCO : {nom}**[^1]

## Conditions et points de vigilance
(conditions du barème + alertes de calcul.py)

## Prochaines étapes
1. Vérifier le solde disponible dans l'espace adhérent de l'OPCO. 2. Construire la formation et
choisir l'organisme partenaire en fonction du budget. 3. Déposer la demande de prise en charge
avant le début de la formation.

## Sources
[^1]: Table SIRET-OPCO, France compétences — {url}
[^2]: Barème {OPCO} {année} — {url}, consulté le {date}
[^3]: Prix communiqué par l'utilisateur (si fourni)
```
