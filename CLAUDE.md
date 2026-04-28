# AeroWatch — CLAUDE.md

Veille automatisée des offres de recrutement PNT (Pilotes) en aviation d'affaires, principalement Europe francophone.

## Ce que fait le projet

Scanner périodique (toutes les 12h) qui agrège les offres pilote de plusieurs compagnies et ATS, les stocke en SQLite, détecte les nouveautés (delta par hash), et notifie Discord uniquement sur les nouvelles offres. Interface web avec liste filtrée + carte Leaflet.

---

## Stack

- **Backend** : Python / FastAPI + APScheduler
- **Scraping** : `requests` + `BeautifulSoup` (HTML) ou appels API directe (JSON)
- **Stockage** : SQLite (`aerowatch.db`) via `sqlite3`
- **Geocodage** : dict statique (fast path) + Nominatim/geopy (fallback, rate-limité)
- **Notifications** : Discord Webhook — uniquement sur les nouvelles offres
- **Frontend** : HTML/CSS/JS vanilla, Leaflet pour la carte
- **Config** : `.env` pour `DISCORD_WEBHOOK_URL`
- **Dev** : `uvicorn main:app --host 0.0.0.0 --port 8000`

---

## Architecture

```
main.py              FastAPI routes + lifespan (scheduler)
scanner.py           Orchestrateur : lance les scrapers, gère delta + expiry
storage.py           CRUD SQLite
models.py            Dataclass JobOffer
geocoder.py          get_coords(location) → (lat, lon)
notifications.py     send_new_jobs(jobs) → Discord
scrapers/
  ats/
    bamboohr.py      scan(slug, name, default_loc) — générique BambooHR
    recruitee.py     scan(slug, name, default_loc) — générique Recruitee
    smartrecruiters.py scan(slug, name, default_loc) — générique SmartRecruiters
  companies/
    amelia.py        scan() — API custom career.flyamelia.com
    netjets.py       scan() — SAP SuccessFactors HTML
    la_compagnie.py  scan() — WeRecruit HTML
    chalair.py       scan() — WordPress HTML statique
    oyonnair.py      scan() — WordPress HTML statique
    pan_europeenne.py scan() — WordPress HTML statique
    volotea.py       scan() — SmartRecruiters
    # ... nouvelles compagnies ici
```

---

## SQLite Schema

```sql
jobs (
    id          TEXT PRIMARY KEY,   -- SHA256[:20](title||link)
    title       TEXT,
    link        TEXT,
    location    TEXT,
    source      TEXT,
    status      TEXT,               -- active | full | expired
    lat         REAL,
    lon         REAL,
    first_seen  TEXT,               -- ISO datetime
    last_seen   TEXT,               -- mis à jour à chaque scan
    notified    INTEGER DEFAULT 0   -- 1 si Discord notifié
)
geocache (location TEXT PK, lat REAL, lon REAL)
meta     (key TEXT PK, value TEXT)  -- last_scan, next_scan
```

---

## Delta detection

Logique dans `scanner.py` :
1. Scraper retourne `list[JobOffer]` ou `None` (erreur réseau → pas d'expiry)
2. `upsert_job(job)` → `True` si nouvelle offre (insert), `False` si update
3. `expire_missing_jobs(source, seen_ids)` → passe les jobs absents en `expired`
4. Discord notifié uniquement sur les jobs ayant retourné `True`

---

## Sources

| Compagnie | Méthode | Module | Status |
|---|---|---|---|
| Jetfly | BambooHR API | `ats/bamboohr.py` | ✅ |
| Comlux | BambooHR API | `ats/bamboohr.py` | ✅ |
| DC Aviation | Recruitee API | `ats/recruitee.py` | ✅ |
| Amelia | API custom | `companies/amelia.py` | ✅ |
| NetJets Europe | SAP SuccessFactors HTML | `companies/netjets.py` | ✅ |
| La Compagnie | WeRecruit HTML | `companies/la_compagnie.py` | ✅ |
| Chalair | WordPress HTML | `companies/chalair.py` | ✅ |
| Oyonnair | — | — | ⛔ Faux positifs : page statique avec catégories permanentes (pas de vraies offres, email only : ops@oyonnair.com) |
| Pan Européenne | WordPress HTML | `companies/pan_europeenne.py` | ✅ |
| Volotea | SmartRecruiters API | `companies/volotea.py` | ✅ |
| VistaJet | iCIMS | — | ⏳ Auth complexe |
| Jet Aviation | SAP SuccessFactors | — | ⏳ Auth complexe |
| Platoon Aviation | JS pur (ATS inconnu) | — | ⏳ Playwright requis |
| Luxaviation | ATS inconnu (migration en cours) | — | ⏳ |
| TAG Aviation | ATS inconnu | — | ⏳ |

---

## Ajouter une nouvelle compagnie

**Si elle utilise un ATS connu :**

```python
# scanner.py → BAMBOOHR_COMPANIES (ou RECRUITEE_COMPANIES, SMARTRECRUITERS_COMPANIES)
BAMBOOHR_COMPANIES = [
    ("jetfly",  "Jetfly",  "Luxembourg"),
    ("comlux",  "Comlux",  "Luxembourg"),
    ("newco",   "NewCo",   "Paris"),    # ← ajouter ici
]
```

**Si elle a un scraper custom :**
1. Créer `scrapers/companies/newco.py` avec `def scan() -> list[JobOffer] | None`
2. L'importer dans `scanner.py` et l'appeler dans `run_scan()`

---

## ATS patterns

```
BambooHR       → {slug}.bamboohr.com/careers/list          (JSON)
Recruitee      → {slug}.recruitee.com/api/offers/           (JSON)
SmartRecruiters→ api.smartrecruiters.com/v1/companies/{slug}/postings (JSON)
Greenhouse     → boards-api.greenhouse.io/v1/boards/{slug}/jobs       (JSON)
Lever          → api.lever.co/v0/postings/{slug}?mode=json             (JSON)
Teamtailor     → {slug}.teamtailor.com/jobs.json                       (JSON)
WeRecruit      → careers.werecruit.io/fr/{slug}/            (HTML statique)
SAP SuccessFactors → HTML scraping uniquement (auth enterprise)
iCIMS          → HTML scraping uniquement (auth enterprise)
```

Pour identifier l'ATS d'un site : F12 → Réseau → XHR → recharger la page carrières.

---

## Conventions

- Chaque scraper expose `scan() -> list[JobOffer] | None` (None = erreur réseau, pas d'expiry)
- Filtres PNT : regex `\b(pilot|captain|first officer|...)\b` — word boundaries obligatoires pour éviter `office ⊂ officer`
- Pas de `print()` — utiliser `logging`
- Les coordonnées GPS sont toujours via `geocoder.get_coords()`, jamais hardcodées dans les scrapers
- Discord ne notifie jamais la liste complète — uniquement les nouveautés détectées par delta hash

---

## Bugs connus / limites

- **PCC** : retourne des catégories, pas des offres réelles — supprimé
- **Oyonnair** : processus email uniquement, pas d'ATS — scraper surveille la page texte
- **Pan Européenne** : idem, email uniquement — scraper surveille le statut
- **Clair Group** : timeouts fréquents, pas d'ATS identifié
