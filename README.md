# ✈️ AeroWatch — Veille Recrutement PNT

Dashboard web de veille des offres pilotes en Europe. Scan automatique toutes les 12h + bouton de refresh manuel. Notifications Discord conservées.

## 🚀 Installation

```bash
# Cloner / placer les fichiers dans un dossier
cd aero-monitor

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn main:app --host 0.0.0.0 --port 8000
```

Le dashboard est ensuite accessible sur : **http://localhost:8000**

## 📁 Structure

```
aero-monitor/
├── main.py           # Backend FastAPI + scrapers + scheduler
├── index.html        # Frontend (servi par FastAPI)
├── requirements.txt
└── jobs_data.json    # Données persistées (créé automatiquement)
```

## 🔧 Configuration

Dans `main.py`, modifier si besoin :
- `DISCORD_WEBHOOK_URL` — votre webhook Discord
- `CHECK_INTERVAL_HOURS` — fréquence des scans auto (défaut : 12h)

## 🌐 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/jobs` | Liste des offres (filtres: `source`, `status`, `q`) |
| `GET /api/sources` | Liste des sources disponibles |
| `GET /api/status` | Statut général + stats |
| `POST /api/scan` | Déclencher un scan manuel |

## 🏢 Sources surveillées

- Oyonnair
- Pan Européenne
- Clair Group (AstonJet/Fly)
- Chalair
- Jetfly
- NetJets Europe
- Pilot Career Center (PCC)
