# skill.md — Règles de collaboration WingJobs

## Compréhension du besoin

- **< 95% de certitude** sur le besoin exprimé → poser des questions avant de coder
- Reformuler le besoin en une phrase avant d'agir si la demande est ambiguë
- Ne jamais supposer l'ATS cible d'une nouvelle compagnie sans preuve (F12 → XHR)

## Avant d'écrire du code

- Inspecter la page cible (WebFetch ou Playwright debug) avant d'écrire le scraper
- Vérifier que les offres trouvées sont de vraies offres ouvertes, pas des candidatures spontanées permanentes
- Si le site retourne 0 résultat au test → distinguer "scraper cassé" vs "pas de poste actuellement"

## Style de réponse

- Réponses courtes et directes — pas de résumé en fin de message
- Pas de bullet points pour des réponses simples
- Signaler les résultats de test immédiatement, sans reformuler ce qui vient d'être fait
- Pas d'émojis
- Ne va pas dans mon sens constamment, challenge mes idées si tu penses que je me trompe

## Code

- Pas de commentaires sauf si le WHY est non-obvious
- Pas de gestion d'erreur pour des cas impossibles
- Suivre le pattern canonique `scan() -> list[JobOffer] | None` sans dévier
- `PILOT_RE` avec word boundaries obligatoires (`\b`)
- Coordonnées GPS toujours via `geocoder.get_coords()`, jamais hardcodées

## Mémoire & contexte

- Mettre à jour `CLAUDE.md` et `Archi.md` après chaque nouvelle compagnie ajoutée
- Mettre à jour le compteur de compagnies dans `Landing.jsx` (STATS) et `Archi.md`
- Ajouter une entrée mémoire si une décision d'architecture non-évidente est prise

## Checklist ajout d'une nouvelle source

1. Identifier l'ATS (F12 → Réseau → XHR)
2. Tester `scan()` manuellement → vérifier que les offres sont réelles
3. Ajouter dans `scanner.py` (BAMBOOHR / RECRUITEE / CUSTOM)
4. Mettre à jour `CLAUDE.md` table sources + compteur
5. Mettre à jour `Landing.jsx` STATS (valeur "26" → N)
6. Mettre à jour `Archi.md` si décision notable
