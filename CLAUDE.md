# AeroWatch — CLAUDE.md

Veille automatisée des offres de recrutement PNT (Pilotes) en aviation d'affaires, principalement Europe francophone.

## Ce que fait le projet

Scanner périodique (toutes les 12h) qui agrège les offres pilote de plusieurs compagnies et ATS, les stocke en SQLite, détecte les nouveautés (delta par hash), et notifie Discord uniquement sur les nouvelles offres. Interface React avec liste filtrée + carte Leaflet.

---

## Principe fondamental

**Qualité avant quantité.** On ne rajoute pas une source si elle génère du bruit (faux positifs, candidatures spontanées permanentes, données ambiguës). Chaque scraper ajouté doit être propre, testé, et retourner uniquement de vraies offres ouvertes. Un scraper qui doute retourne `None`, pas une liste vide inventée.

---

## Stack

- **Backend** : Python / FastAPI + APScheduler — dossier `backend/`
- **Frontend** : React + Vite + react-leaflet — dossier `frontend/`
- **Scraping** : `requests` + `BeautifulSoup` (HTML) ou appels API directe (JSON)
- **Stockage** : SQLite (`aerowatch.db`) via `sqlite3`
- **Geocodage** : dict statique (fast path) + Nominatim/geopy (fallback, rate-limité, caché en base)
- **Notifications** : Discord Webhook — uniquement sur les nouvelles offres
- **Config** : `.env` pour `DISCORD_WEBHOOK_URL`
- **Dev** : `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload` + `cd frontend && npm run dev`

---

## Architecture

```
backend/
  main.py              FastAPI routes + lifespan (scheduler) + StaticFiles (prod)
  scanner.py           Orchestrateur : lance les scrapers, gère delta + expiry
  storage.py           CRUD SQLite
  models.py            Dataclass JobOffer
  geocoder.py          get_coords(location) → (lat, lon)
  notifications.py     send_new_jobs(jobs) → Discord
  scrapers/
    ats/
      bamboohr.py      scan(slug, name, default_loc) — générique BambooHR
      recruitee.py     scan(slug, name, default_loc) — générique Recruitee
    companies/
      amelia.py        scan() — API custom career.flyamelia.com
      netjets.py       scan() — SAP SuccessFactors HTML (netjets.jobs.hr.cloud.sap)
      la_compagnie.py  scan() — WeRecruit HTML
      chalair.py       scan() — WordPress HTML statique
      pan_europeenne.py scan() — sentinel statut (email only, surveille "no employment")
      helvetic.py      scan() — portal custom career.helvetic.com, surveille /flightcrew
      # ... nouvelles compagnies ici

frontend/
  src/
    App.jsx            Layout principal, état global, drag handle
    api.js             Appels fetch centralisés (/api/jobs, /sources, /status, /scanner)
    index.css          Thème dark complet (variables CSS, composants)
    components/
      Header.jsx       Logo + stats (actives/total/nouvelles) + bouton scan
      FilterBar.jsx    Recherche texte + chips source + chips statut
      ScannerStatus.jsx  Panel collapsible, dot par source (ok-jobs/ok-empty/error)
      JobList.jsx      Groupé par source, scroll
      JobCard.jsx      Dot statut, badges, lien
      MapPanel.jsx     Leaflet, markers SVG colorés, invalidateSize au montage
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
geocache     (location TEXT PK, lat REAL, lon REAL)
meta         (key TEXT PK, value TEXT)       -- last_scan, next_scan
source_status(source TEXT PK, last_check TEXT, status TEXT,
              jobs_found INT, duration_ms INT, error_msg TEXT)
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
| Luxaviation | BambooHR API | `ats/bamboohr.py` | ✅ — lent au 1er scan (geocoding), cache ensuite |
| DC Aviation | Recruitee API | `ats/recruitee.py` | ✅ |
| Amelia | API custom | `companies/amelia.py` | ✅ |
| NetJets Europe | SAP SuccessFactors HTML | `companies/netjets.py` | ✅ — lien sur `netjets.jobs.hr.cloud.sap` |
| La Compagnie | WeRecruit HTML | `companies/la_compagnie.py` | ✅ |
| Chalair | WordPress HTML | `companies/chalair.py` | ✅ — filtre "candidature spontanée" actif |
| Pan Européenne | sentinel statut | `companies/pan_europeenne.py` | ✅ — retourne `status=full` si "no employment" |
| TAG Aviation | Recruitee API | `ats/recruitee.py` | ✅ — slug `tagaviation3`, postes globaux (HK, Malaisie…) |
| Helvetic Airways | Portal custom HTML | `companies/helvetic.py` | ✅ — 0 poste en ce moment, se déclenche dès ouverture |
| Oyonnair | — | — | ⛔ Email only, faux positifs (catégories permanentes) — supprimé |
| Twin Jet | — | — | ⛔ Email only (`recrutement.pnt@twinjet.net`) |
| Air Hamburg | — | — | ⛔ Groupe Vista Global, bloqué Cloudflare |
| Volotea | — | — | ⛔ SmartRecruiters slug invalide, page careers inaccessible |
| ASL Airlines | CezanneHR | — | ⛔ Pas d'API JSON, HTML sans postes pilote identifiables |
| VistaJet | iCIMS | — | ⏳ Auth complexe |
| Jet Aviation | SAP SuccessFactors | — | ⏳ Auth complexe |
| Platoon Aviation | JS pur | — | ⏳ Playwright requis |

---

## Ajouter une nouvelle compagnie

**Si elle utilise un ATS connu :**

```python
# scanner.py → BAMBOOHR_COMPANIES (ou RECRUITEE_COMPANIES)
BAMBOOHR_COMPANIES = [
    ("jetfly",      "Jetfly",      "Luxembourg"),
    ("comlux",      "Comlux",      "Luxembourg"),
    ("luxaviation", "Luxaviation", "Luxembourg"),
    ("newco",       "NewCo",       "Paris"),    # ← ajouter ici
]

RECRUITEE_COMPANIES = [
    ("dcaviationgmbh", "DC Aviation",  "Stuttgart"),
    ("tagaviation3",   "TAG Aviation", "Geneva"),
    ("newco",          "NewCo",        "Paris"),  # ← ajouter ici
]
```

**Si elle a un scraper custom :**
1. Créer `scrapers/companies/newco.py` avec `def scan() -> list[JobOffer] | None`
2. L'importer dans `scanner.py` et l'appeler dans `run_scan()`

**Avant d'ajouter :** vérifier manuellement que l'API retourne de vraies offres ouvertes, pas des catégories ou candidatures spontanées permanentes.

---

## ATS patterns

```
BambooHR        → {slug}.bamboohr.com/careers/list                        (JSON)
Recruitee       → {slug}.recruitee.com/api/offers/                        (JSON)
SmartRecruiters → api.smartrecruiters.com/v1/companies/{slug}/postings    (JSON)
Greenhouse      → boards-api.greenhouse.io/v1/boards/{slug}/jobs           (JSON)
Lever           → api.lever.co/v0/postings/{slug}?mode=json                (JSON)
Teamtailor      → {slug}.teamtailor.com/jobs.json                          (JSON)
WeRecruit       → careers.werecruit.io/fr/{slug}/                          (HTML)
SAP SuccessFactors → HTML scraping uniquement (auth enterprise)
iCIMS           → HTML scraping uniquement (auth enterprise)
```

Pour identifier l'ATS d'un site : F12 → Réseau → XHR → recharger la page carrières.

---

## Conventions

- Chaque scraper expose `scan() -> list[JobOffer] | None` (None = erreur réseau, pas d'expiry)
- Filtres PNT : regex `\b(pilot|captain|first officer|...)\b` — word boundaries obligatoires pour éviter `office ⊂ officer`
- Exclure explicitement les faux positifs : `EXCLUDE_KW` dans chaque scraper si nécessaire
- Pas de `print()` — utiliser `logging`
- Les coordonnées GPS sont toujours via `geocoder.get_coords()`, jamais hardcodées dans les scrapers
- Discord ne notifie jamais la liste complète — uniquement les nouveautés détectées par delta hash
- Les liens doivent pointer vers le bon domaine (ex : `netjets.jobs.hr.cloud.sap`, pas `careers.netjets.com`)

---

## Bugs connus / limites

- **Luxaviation** : 1er scan lent (~60s) car geocoding Nominatim pour Dubai, Kuala Lumpur, etc. — résolu après mise en cache
- **Pan Européenne** : sentinel volontaire — "Effectifs complets" en `status=full` est le comportement attendu
- **Chalair** : scraper actif mais ne retournera des offres que si de vraies positions PNT sont publiées (candidatures spontanées filtrées)
- **NetJets** : lien sur `netjets.jobs.hr.cloud.sap` (SAP), pas sur `careers.netjets.com`
- **Helvetic** : portal Apache Wicket avec session IDs dans les URLs de page, mais les ancres `#id` des postes sont stables — scrape `/flightcrew` sans session
- **TAG Aviation** : slug Recruitee = `tagaviation3` (pas `tagaviation`)
