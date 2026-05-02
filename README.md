# WingJobs

Veille automatisée des offres de recrutement PNT en aviation d'affaires européenne. Scan de 20 compagnies toutes les 12h, détection des nouvelles offres par delta de hash, notifications Discord uniquement sur les vraies nouveautés.

---

## Fonctionnement

- **Agrège** les offres pilotes de 20 opérateurs européens — APIs BambooHR, Recruitee, CSOD, iCIMS, SAP SuccessFactors, portails custom et pages WordPress
- **Détecte les changements** par hachage SHA-256 : seules les nouvelles offres déclenchent une notification Discord, zéro spam
- **Expire automatiquement** les offres disparues de la source lors du scan suivant
- **Visualise** tous les postes actifs sur une carte Leaflet interactive avec marqueurs colorés par statut
- **S'auto-héberge** en un seul conteneur Docker derrière Caddy — aucune base externe, SQLite uniquement

## Stack

| Couche | Technologie |
|---|---|
| Backend | Python · FastAPI · APScheduler |
| Scraping | requests · BeautifulSoup · APIs ATS directes |
| Stockage | SQLite (offres, géocache, statut sources) |
| Frontend | React · Vite · react-leaflet |
| Notifications | Discord Webhook |
| Déploiement | Docker · Caddy (reverse proxy + SSL auto) |

## Sources surveillées

| Compagnie | Pays | Méthode |
|---|---|---|
| Jetfly | LU | BambooHR API |
| Comlux | LU | BambooHR API |
| Luxaviation | LU/EU | BambooHR API |
| DC Aviation | DE | Recruitee API |
| TAG Aviation | CH | Recruitee API |
| Amelia | FR | API custom |
| NetJets Europe | PT | SAP SuccessFactors HTML |
| La Compagnie | FR | WeRecruit HTML |
| Chalair | FR | WordPress HTML |
| Pan Européenne | FR | Sentinel statut |
| Helvetic Airways | CH | Portail custom HTML |
| Elit'Avia | EU | WordPress Elementor HTML |
| Avcon Jet | AT | WordPress HTML |
| Flying Group | BE | WordPress REST API |
| Air Alliance | DE | Portail custom HTML |
| Danish Air Transport | DK | WordPress HTML |
| Loganair | UK | Salesforce Recruit HTML |
| Jet Aviation | EU | SAP SuccessFactors custom |
| VistaJet | EU | iCIMS HTML |
| Luxair | LU | Cornerstone OnDemand API |

## Interface

**Desktop** — panneau gauche (liste filtrée) + panneau droit (carte), séparateur déplaçable à la souris.

**Mobile** — navigation par onglets entre liste et carte. Un tap sur une offre fait voler la carte vers sa position.

Le panneau scanner affiche un dot de statut en temps réel par source (offres trouvées / vide / erreur).

## Lancer en local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (terminal séparé)
cd frontend
npm install
npm run dev
```

## Déployer (Docker + Caddy)

```bash
# Build et démarrage
docker compose up -d --build

# Ajouter au Caddyfile existant
jobs.wingfuel.fr {
    reverse_proxy wingjobs:8000
}
```

Les données sont persistées dans un volume nommé (`wingjobs-data`). 

## Configuration

| Variable | Défaut | Description |
|---|---|---|
| `DISCORD_WEBHOOK_URL` | — | Webhook Discord pour les alertes nouvelles offres |
| `DB_FILE` | `wingjobs.db` | Chemin SQLite (Docker : `/app/data/wingjobs.db`) |
| `CHECK_INTERVAL_HOURS` | `12` | Fréquence des scans automatiques |

## API

| Endpoint | Description |
|---|---|
| `GET /api/jobs` | Toutes les offres — filtrables par `source`, `status`, `q` |
| `GET /api/sources` | Liste des sources connues |
| `GET /api/status` | Horodatages dernier/prochain scan + statut par source |
| `POST /api/scanner/run` | Déclencher un scan manuel |
