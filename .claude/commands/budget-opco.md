---
description: Estime le budget OPCO annuel d'une entreprise pour financer une formation et produit une fiche sourcée
argument-hint: "<nom, SIREN ou site web de l'entreprise>" [prix HT total] [heures]
allowed-tools: Bash(python3 scripts/*), Read, Write, Agent, WebFetch
---

Entreprise : $1 · Prix HT total : $2 (facultatif) · Heures : $3 (facultatif)

Objectif : afficher le **budget OPCO** que l'entreprise peut mobiliser cette année et, si un prix est
fourni, le **reste à charge**. Sans prix, n'invente aucun prix et n'affiche pas de reste à charge.

Déroule les étapes dans l'ordre, sans en sauter.

1. **Identifier l'entreprise.** Si l'entrée est un SIREN (9 chiffres) ou un SIRET (14 chiffres),
   passe à l'étape 2. Si c'est un site web (domaine ou URL), lis ses mentions légales avec WebFetch
   (essaie `/mentions-legales`, puis le lien « Mentions légales » de la page d'accueil) pour y relever
   le SIREN ou, à défaut, la raison sociale ; le nom commercial du site n'est pas fiable. Sinon, lance
   `python3 scripts/entreprise.py chercher "<nom>"`.
   - Un seul candidat clairement pertinent : retiens-le.
   - Plusieurs candidats : affiche-les dans un tableau (nom, ville, NAF, effectif, SIREN) et demande
     lequel choisir. Arrête-toi là jusqu'à la réponse.
2. **Fiche officielle.** Lance `python3 scripts/entreprise.py fiche <SIREN>` et enregistre la sortie
   dans `travail/<SIREN>.json`. Si `opco.statut` vaut « non trouvé » ou « plusieurs OPCO », signale-le
   et demande comment continuer.
3. **Barème.** Les critères dépendent de la branche : la clé du cache est l'OPCO **et** l'IDCC.
   Si `data/baremes/<OPCO>-<IDCC>-<ANNÉE>.json` existe et que sa `date_consultation` a moins de
   30 jours, réutilise-le. Sinon, délègue au sous-agent `veille-bareme` en lui donnant l'OPCO,
   l'année en cours, l'IDCC et ce chemin de fichier. Les espaces du nom de l'OPCO deviennent des
   tirets dans le nom du fichier.
4. **Calcul.** Lance `python3 scripts/calcul.py --entreprise travail/<SIREN>.json --bareme <barème>`, en ajoutant
   `--prix <prix>` et `--heures <heures>` s'ils sont fournis.
   N'effectue aucun calcul toi-même : le montant vient de ce script.
5. **Fiche.** Écris `sorties/fiche-<nom-en-minuscules-avec-tirets>.md` selon le gabarit de
   CLAUDE.md, puis affiche dans le chat un résumé court : OPCO, budget OPCO estimé, niveau de
   confiance, et le reste à charge si un prix a été fourni.
