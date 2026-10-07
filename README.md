# Budget OPCO — un agent Claude Code de bout en bout

> Projet de démonstration de Vincent Duchemin (Cizel), formateur IA / Claude Code agentique.

**Le problème.** Un dirigeant de TPE veut se former à l'IA, mais ne sait ni quel est son OPCO, ni
combien celui-ci finance. Trouver la réponse demande 20 à 40 minutes de recherche : convention
collective, table des OPCO, barème de branche…

**La solution.** Deux portes d'entrée :
- **Une interface web** (`web/`, déployée sur Netlify) : on tape un nom, un SIREN ou un site web et on obtient
  l'OPCO et le budget en direct, avec les barèmes déjà constitués. Aucun serveur ni clé d'API.
- **Un agent Claude Code** qui va plus loin : il identifie l'entreprise depuis ses mentions légales,
  **recherche lui-même** le barème d'une branche inconnue, puis produit une fiche sourcée.

Côté agent, une seule commande :

```
/budget-opco "Nom de l'entreprise" [prix HT] [heures]
```

→ en 1 à 2 minutes, une fiche sourcée : OPCO officiel, budget OPCO estimé pour l'année, reste à charge si un prix est donné,
conditions et prochaines étapes. La formation se construit ensuite à la mesure de ce budget. Voir un exemple dans `sorties/`.

## Ce que le projet démontre

| Concept Claude Code | Où | Ce qu'il illustre |
|---|---|---|
| **CLAUDE.md** | `CLAUDE.md` | Mémoire du projet : règles métier, répartition du travail, gabarit de sortie |
| **Commande personnalisée** | `.claude/commands/budget-opco.md` | Un processus métier en 5 étapes, déclenché par un seul mot, avec arguments |
| **Sous-agent** | `.claude/agents/veille-bareme.md` | Recherche web déléguée, dans un contexte isolé, sur un modèle moins cher (Sonnet) |
| **Scripts déterministes** | `scripts/` | Ce qui doit être exact (API officielles, calcul) n'est **pas** confié au LLM |
| **Hook** | `.claude/hooks/verifier_sources.py` | Un garde-fou automatique : une fiche contenant un montant sans source est refusée |
| **Permissions** | `.claude/settings.json` | Le strict nécessaire est autorisé, pour une démo sans interruption |
| **Interface sans serveur** | `web/index.html` | Les barèmes produits par l'agent alimentent une page statique (`scripts/exporter_baremes.py`) |
| **Cache** | `data/baremes/` | Un barème trouvé (par OPCO et par branche) est réutilisé pendant 30 jours, donc moins de coût et plus de stabilité |

**Le principe pédagogique central :** *le LLM orchestre et interprète ; le code calcule ; le hook vérifie.*

## Comment ça marche

```
"Nom de l'entreprise"
   │
   ▼  scripts/entreprise.py ──► API Recherche d'entreprises (SIREN, effectif, IDCC)
   │                       └──► Table SIRET-OPCO, France compétences (OPCO officiel)
   ▼  sous-agent veille-bareme ──► site de l'OPCO (critères de l'année, sourcés)
   ▼  scripts/calcul.py ──► effectif + barème = budget OPCO annuel
   ▼  fiche Markdown ──► hook : chaque montant a-t-il sa source ? sinon refus et correction
sorties/fiche-<entreprise>.md
```

## Installation et démo

Prérequis : Claude Code et Python 3 (aucune dépendance, aucune clé d'API : les données sont publiques).
Au premier lancement, ouvrez `claude` dans le dossier et acceptez la demande de confiance : sinon les
permissions et le hook du projet sont ignorés.

```bash
cd <dossier-du-projet>
claude
```
Puis, dans Claude Code : `/budget-opco "nom d'une TPE"`.

Scénario de démo conseillé (5 min) :
1. Lancer la commande sur une TPE connue de l'auditoire.
2. Montrer la gestion des homonymes (l'agent demande de choisir).
3. Ouvrir la fiche, cliquer sur une source.
4. Montrer le hook : demander à Claude d'« arrondir le montant sans source », et constater le refus.
5. Relancer sur une entreprise de plus de 50 salariés : l'outil ne promet rien et propose des alternatives.

Interface en local :

```bash
python3 scripts/exporter_baremes.py && python3 -m http.server 8765 --directory web
```

## Exemples
- [`sorties/fiche-one-learn.md`](sorties/fiche-one-learn.md) : AKTO, 4 500 € HT par an, fonds de la branche signalés épuisés.
- [`sorties/fiche-competences-et-savoir.md`](sorties/fiche-competences-et-savoir.md) : identifiée depuis le site
  competences-savoir.fr, barème AKTO réutilisé depuis le cache.

## Limites assumées
- **C'est une estimation.** Seul l'OPCO décide, et le plafond annuel a pu être déjà consommé.
- La tranche d'effectif INSEE peut dater de 1 à 2 ans.
- Les barèmes changent chaque année et parfois en cours d'année (fonds épuisés) : la date de
  consultation est toujours affichée.
- Le financement OPCO exige un organisme certifié Qualiopi : la formation est portée par un
  organisme partenaire, choisi selon le budget.

## Pistes d'exercices (atelier)
1. Ajouter un catalogue de formations et proposer celle qui correspond au budget trouvé.
2. Écrire un hook `PostToolUse` qui journalise chaque recherche web du sous-agent.
3. Transformer la commande en *skill* qui se déclenche dès qu'on parle de financement de formation.
4. Ajouter le cas du salarié : CPF (estimation des droits) et reste à charge obligatoire.
