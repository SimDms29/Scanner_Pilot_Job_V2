# Archi.md — WingJobs

## Pattern scraper canonique

```python
# scrapers/companies/newco.py
PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|f/o|...)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|steward|maintenance|...)\b', re.I)

def scan() -> list[JobOffer] | None:
    # None = erreur réseau → pas d'expiry côté scanner.py
    # []   = succès, aucun poste pilote
    try:
        ...
        return found
    except Exception as e:
        log.error(f"Erreur NewCo: {e}")
        return None
```

Enregistrer dans `scanner.py` → `CUSTOM_SCRAPERS` (ou `BAMBOOHR_COMPANIES` / `RECRUITEE_COMPANIES`).

---

## Décisions d'architecture

| Décision | Choix retenu | Pourquoi |
|---|---|---|
| Filtre Captain/FO | Client-side `useMemo` | Dataset < 200 offres, pas besoin param API |
| Notifications | Supprimé (Discord) | Discord non ouvert au public |
| URL GlobalJet | Slugification titre → hash | Pas de href sur les boutons, hash stable |
| Geocoding | Dict statique + Nominatim fallback | Rapide pour les villes connues, cache SQLite ensuite |
| Playwright | Uniquement si rendu JS pur | `requests`+BS4 suffisent dans 90% des cas |

---

## ATS → méthode rapide

| ATS | Indice visuel | Méthode |
|---|---|---|
| BambooHR | `*.bamboohr.com` | JSON API directe |
| Recruitee | `*.recruitee.com` | JSON API directe |
| Personio | `*.personio.de/xml` | XML feed public |
| Salesforce Lightning | `#JobOfferSearchContainer` vide | Playwright obligatoire |
| Drupal Views AJAX | `.vacancies__item` vide | Playwright obligatoire |
| SAP SuccessFactors | `*.cloud.sap` | HTML scraping |
| iCIMS | `hub-*.icims.com` | HTML + `?in_iframe=1` |
| Cornerstone (CSOD) | token JWT dans XHR | Récupérer token dynamiquement |

---

## SQLite — tables clés

```
jobs          → id(SHA256[:20]), title, link, location, source, status, lat, lon, first_seen, last_seen, notified
geocache      → location(PK), lat, lon
meta          → key(PK), value  [last_scan, next_scan]
source_status → source(PK), last_check, status, jobs_found, duration_ms, error_msg
```

---

## Frontend — état global (Scanner.jsx)

```
filters: { q, source, status='active', role='' }
jobs (API) → visibleJobs (useMemo, filtre role client-side) → JobList + MapPanel
```

---

## Commandes dev

```bash
cd backend  && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
cd frontend && npm run dev
python -c "from scrapers.companies import newco; print(newco.scan())"  # tester un scraper
```
