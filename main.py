from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
import threading

load_dotenv()

app = FastAPI(title="Aero Job Monitor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not DISCORD_WEBHOOK_URL:
    print("⚠️  DISCORD_WEBHOOK_URL manquant dans le .env — notifications Discord désactivées.")
CHECK_INTERVAL_HOURS = 12
DATA_FILE = "jobs_data.json"

# Coordonnées par ville/région
LOCATION_COORDS = {
    # France
    "paris cdg": (49.0097, 2.5478),
    "paris orly": (48.7262, 2.3652),
    "paris": (48.8566, 2.3522),
    "le bourget": (48.9697, 2.4411),
    "guyancourt": (48.7729, 2.0696),
    "nice": (43.7102, 7.2620),
    "lyon": (45.7640, 4.8357),
    "marseille": (43.2965, 5.3698),
    "toulouse": (43.6047, 1.4442),
    "rennes": (48.1173, -1.6778),
    "nantes": (47.2184, -1.5536),
    "bordeaux": (44.8378, -0.5792),
    "brest": (48.3904, -4.4861),
    "bâle-mulhouse": (47.5896, 7.5290),
    "chambéry": (45.5646, 5.9178),
    "chambery": (45.5646, 5.9178),
        "clermont-ferrand": (45.7772, 3.0870),

    "france": (46.2276, 2.2137),
    # Suisse
    "genève": (46.2044, 6.1432),
    "geneve": (46.2044, 6.1432),
    "zurich": (47.3769, 8.5417),
    "berne": (46.9481, 7.4474),
    "lugano": (46.0037, 8.9511),
    "meyrin": (46.2338, 6.0622),
        "lausanne": (46.5197, 6.6323),

    # Belgique
    "bruxelles": (50.8503, 4.3517),
    "charleroi": (50.4614, 4.4446),
    "liège": (50.6292, 5.5797),
    "liege": (50.6292, 5.5797),
    "belgium": (50.8503, 4.3517),
    # Luxembourg
    "luxembourg": (49.6117, 6.1319),
    # Allemagne
    "francfort": (50.1109, 8.6821),
    "munich": (48.1351, 11.5820),
    "berlin": (52.5200, 13.4050),
    "düsseldorf": (51.2217, 6.7762),
    "dusseldorf": (51.2217, 6.7762),
    "cologne": (50.9333, 6.9500),
    "stuttgart": (48.7758, 9.1829),
    "hambourg": (53.5753, 10.0153),
    "zweibrücken": (49.2092, 7.3600),
    "zweibrucken": (49.2092, 7.3600),
    # Pays-Bas
    "amsterdam": (52.3676, 4.9041),
    # UK
    "londres heathrow": (51.4700, -0.4543),
    "londres gatwick": (51.1537, -0.1821),
    "londres city": (51.5048, 0.0495),
    "londres": (51.5074, -0.1278),
    "london": (51.5074, -0.1278),
    "oxford": (51.7520, -1.2577),
    "manchester": (53.3498, -2.2799),
    "gb": (51.5074, -0.1278),
    # Espagne
    "madrid": (40.4168, -3.7038),
    "barcelone": (41.3851, 2.1734),
    # Portugal
    "lisbonne": (38.7223, -9.1393),
    "lisbon": (38.7223, -9.1393),
    # Italie
    "milan malpensa": (45.6301, 8.7231),
    "milan linate": (45.4449, 9.2766),
    "milan": (45.4654, 9.1859),
    "rome": (41.9028, 12.4964),
    # Autriche
    "vienne": (48.2082, 16.3738),
    # République Tchèque
    "prague": (50.0755, 14.4378),
    # Scandinavie
    "copenhague": (55.6761, 12.5683),
    "oslo": (59.9139, 10.7522),
    "stockholm": (59.3293, 18.0686),
    # Défaut
    "europe": (48.5, 10.0),
    "n/c": (48.5, 10.0),
    # Ajouts compagnies
    "strasbourg": (48.5734, 7.7521),
    "mulhouse": (47.7508, 7.3359),
    "new york": (40.7128, -74.0060),
    "milan": (45.4654, 9.1859),
}

def get_coords(location: str):
    loc_low = location.lower()
    for key, coords in LOCATION_COORDS.items():
        if key in loc_low:
            return coords
    return (48.5, 10.0)

# --- DATA STORE ---
_store = {
    "jobs": [],
    "last_scan": None,
    "next_scan": None,
    "scan_running": False,
}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "jobs": [j.__dict__ for j in _store["jobs"]],
            "last_scan": _store["last_scan"],
            "next_scan": _store["next_scan"],
        }, f)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            data = json.load(f)
            _store["jobs"] = [JobOffer(**j) for j in data.get("jobs", [])]
            _store["last_scan"] = data.get("last_scan")
            _store["next_scan"] = data.get("next_scan")

# --- MODEL ---
class JobOffer:
    def __init__(self, title, link, location="N/C", source="Inconnue", status="active", lat=None, lon=None):
        self.title = title
        self.link = link
        self.location = location
        self.source = source
        self.status = status
        coords = get_coords(location)
        self.lat = lat if lat else coords[0]
        self.lon = lon if lon else coords[1]

# --- SCANNERS ---
def scan_clair_group():
    print("--- Scan Clair Group ---")
    url = "https://www.clair-group.com/fr/recrutement/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    found = []
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text().lower()
            for item in soup.find_all(['h3', 'a', 'div'], class_=['job', 'offer', 'title']):
                text = item.get_text(strip=True).lower()
                if any(k in text for k in ["pilote", "pnt", "commandant", "officier", "captain", "f/o"]):
                    link = item['href'] if item.name == 'a' and item.has_attr('href') else url
                    if not link.startswith('http'):
                        link = "https://www.clair-group.com" + link
                    found.append(JobOffer(text.capitalize(), link, "Le Bourget", "Clair Group"))
            if not found:
                for a in soup.find_all('a', href=True):
                    text = a.get_text(strip=True).lower()
                    if any(k in text for k in ["pilote", "pnt", "captain", "candidature"]):
                        link = a['href']
                        if not link.startswith('http'):
                            link = "https://www.clair-group.com" + link
                        found.append(JobOffer(text.capitalize(), link, "Le Bourget", "Clair Group"))
            if not found and any(k in page_text for k in ["effectifs complets", "pas de recrutement", "no vacancy"]):
                return [JobOffer("Effectifs complets", url, "Le Bourget", "Clair Group", status="full")]
    except Exception as e:
        print(f"Erreur Clair Group: {e}")
    return found

ICAO_IATA_MAP = {
    # Suisse
    "LSGG": "Genève", "GVA": "Genève",
    "LSZH": "Zurich", "ZRH": "Zurich",
    "LSZB": "Berne",
    "LSZA": "Lugano",
        "LSGL": "Lausanne",

    # France
    "LFPG": "Paris CDG", "CDG": "Paris CDG",
    "LFPO": "Paris Orly", "ORY": "Paris Orly",
    "LFPB": "Le Bourget",
    "LFMN": "Nice", "NCE": "Nice",
    "LFLL": "Lyon", "LYS": "Lyon",
    "LFML": "Marseille", "MRS": "Marseille",
    "LFBO": "Toulouse", "TLS": "Toulouse",
    "LFRN": "Rennes", "RNS": "Rennes",
    "LFRS": "Nantes", "NTE": "Nantes",
    "LFSB": "Bâle-Mulhouse", "BSL": "Bâle-Mulhouse",
    "LFBD": "Bordeaux", "BOD": "Bordeaux",
        "LFLC": "Clermont-Ferrand", "CFE": "Clermont-Ferrand",

    
    # Belgique
    "EBBR": "Bruxelles", "BRU": "Bruxelles",
    "EBCI": "Charleroi",
    "EBLG": "Liège",
    # Luxembourg
    "ELLX": "Luxembourg", "LUX": "Luxembourg",
    # Allemagne
    "EDDF": "Francfort", "FRA": "Francfort",
    "EDDM": "Munich", "MUC": "Munich",
    "EDDB": "Berlin", "BER": "Berlin",
    "EDDL": "Düsseldorf", "DUS": "Düsseldorf",
    "EDDK": "Cologne", "CGN": "Cologne",
    "EDDS": "Stuttgart", "STR": "Stuttgart",
    "EDDH": "Hambourg", "HAM": "Hambourg",
    "EDRZ": "Zweibrücken",
    # Pays-Bas
    "EHAM": "Amsterdam", "AMS": "Amsterdam",
    # UK
    "EGLL": "Londres Heathrow", "LHR": "Londres Heathrow",
    "EGKK": "Londres Gatwick", "LGW": "Londres Gatwick",
    "EGLC": "Londres City", "LCY": "Londres City",
    "EGCC": "Manchester", "MAN": "Manchester",
    "EGTK": "Oxford",
    # Espagne
    "LEMD": "Madrid", "MAD": "Madrid",
    "LEBL": "Barcelone", "BCN": "Barcelone",
    # Portugal
    "LPPT": "Lisbonne", "LIS": "Lisbonne",
    # Italie
    "LIRF": "Rome", "FCO": "Rome",
    "LIML": "Milan Linate", "LIN": "Milan Linate",
    "LIMC": "Milan Malpensa", "MXP": "Milan Malpensa",
    # Autriche
    "LOWW": "Vienne", "VIE": "Vienne",
    # République Tchèque
    "LKPR": "Prague", "PRG": "Prague",
    # Scandinavie
    "EKCH": "Copenhague", "CPH": "Copenhague",
    "ENGM": "Oslo", "OSL": "Oslo",
    "ESSA": "Stockholm", "ARN": "Stockholm",
}

def extract_location_from_title(title: str):
    """Cherche un code OACI (4 lettres) ou IATA (3 lettres) dans le titre de l'offre."""
    import re
    words = re.findall(r'\b[A-Z]{3,4}\b', title.upper())
    for word in words:
        if word in ICAO_IATA_MAP:
            return ICAO_IATA_MAP[word]
    return None

def scan_jetfly():
    print("--- Scan Jetfly ---")
    api_url = "https://jetfly.bamboohr.com/careers/list"
    found = []
    try:
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            jobs = r.json().get('result', [])
            for j in jobs:
                title = j.get('jobOpeningName', '')
                title_low = title.lower()
                if any(k in title_low for k in ["pilot", "captain", "first officer", "f/o"]):
                    ops_keywords = ["ground", "dispatch", "ops", "sales", "office", "accountant", "mechanic", "technician"]
                    if not any(ok in title_low for ok in ops_keywords):
                        # 1. Essayer d'extraire le code OACI/IATA depuis le titre (ex: "PILOT PC12 LSGG")
                        loc = extract_location_from_title(title)
                        # 2. Sinon utiliser le champ location de l'API
                        if not loc:
                            raw_loc = j.get('location', {})
                            if isinstance(raw_loc, dict):
                                loc = raw_loc.get('city') or raw_loc.get('state') or 'Luxembourg'
                            else:
                                loc = raw_loc or 'Luxembourg'
                        found.append(JobOffer(title, f"https://jetfly.bamboohr.com/careers/{j.get('id')}", loc, "Jetfly"))
    except Exception as e:
        print(f"Erreur Jetfly: {e}")
    return found

def scan_oyonnair():
    print("--- Scan Oyonnair ---")
    url = "https://www.oyonnair.com/compagnie-aerienne/recrutement/"
    found = []
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text().lower()
            if "effectifs sont complets" in page_text or "effectifs complets" in page_text:
                return [JobOffer("Effectifs complets", url, "Lyon/Rennes", "Oyonnair", status="full")]
            for elem in soup.find_all(['h2', 'h3', 'a']):
                text = elem.get_text(strip=True).lower()
                exclusions = ["régulièrement à la recherche", "rejoignez-nous", "recrutement", "différents domaines", "tels que", "compagnie-aerienne"]
                if any(k in text for k in ["pilote", "pnt", "commandant", "capitaine", "captain"]):
                    if not any(ex in text for ex in exclusions) and len(text) < 100:
                        if elem.name == 'a' and elem.has_attr('href') and 'recrutement' not in elem['href']:
                            link = elem['href']
                            if not link.startswith('http'):
                                link = "https://www.oyonnair.com" + link
                            found.append(JobOffer(text.capitalize(), link, "Lyon", "Oyonnair"))
            seen = set()
            found = [j for j in found if j.title not in seen and not seen.add(j.title)]
    except Exception as e:
        print(f"Erreur Oyonnair: {e}")
    return found

def scan_pan_european():
    print("--- Scan Pan Européenne ---")
    url = "https://www.paneuropeenne.com/en/"
    found = []
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text().lower()
            for elem in soup.find_all(['h2', 'h3', 'h4', 'div', 'p', 'li', 'a']):
                text = elem.get_text(strip=True).lower()
                if any(k in text for k in ["pilot", "captain", "first officer", "f/o", "pnt"]):
                    if len(text) > 10 and len(text) < 200 and "no employment" not in text:
                        link = url
                        if elem.name == 'a' and elem.has_attr('href'):
                            link = elem['href']
                            if not link.startswith('http'):
                                link = "https://www.paneuropeenne.com" + link
                        found.append(JobOffer(text.capitalize(), link, "Chambéry", "Pan Européenne"))
            seen = set()
            found = [j for j in found if j.title not in seen and not seen.add(j.title)]
            if not found and "no employment at the moment" in page_text:
                return [JobOffer("Effectifs complets", url, "Chambéry", "Pan Européenne", status="full")]
    except Exception as e:
        print(f"Erreur Pan Européenne: {e}")
    return found

def scan_chalair():
    print("--- Scan Chalair ---")
    url = "https://www.chalair.fr/offres-emplois"
    found, seen = [], set()
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True).lower()
                href_lower = a['href'].lower()
                if any(k in text or k in href_lower for k in ["candidature", "pnt", "pilote", "captain", "recrutement"]):
                    u = a['href'] if a['href'].startswith('http') else f"https://www.chalair.fr{a['href']}"
                    if u not in seen and len(text) > 5:
                        found.append(JobOffer(text.capitalize() if text else "Candidature PNT", u, "France", "Chalair"))
                        seen.add(u)
    except Exception as e:
        print(f"Erreur Chalair: {e}")
    return found

def scan_netjets():
    print("--- Scan NetJets Europe ---")
    url = "https://netjets.jobs.hr.cloud.sap/europe/search/?createNewAlert=false&q=pilot"
    base_url = "https://netjets.jobs.hr.cloud.sap"
    found = []
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                link_tag = row.find('a', href=True)
                if not link_tag:
                    continue
                title = link_tag.get_text(strip=True)
                href = link_tag['href']
                if not href.startswith('http'):
                    href = base_url + href
                cells = row.find_all('td')
                location = "N/C"
                if len(cells) >= 2:
                    location = cells[1].get_text(strip=True)
                title_low = title.lower()
                if any(k in title_low for k in ["pilot", "captain", "first officer", "second in command", "f/o", "pic", "sic"]):
                    found.append(JobOffer(title, href, location, "NetJets Europe"))
    except Exception as e:
        print(f"Erreur NetJets: {e}")
    return found

def scan_pcc():
    print("--- Scan PCC ---")
    url = "https://pilotcareercenter.com/PILOT-JOB-NAVIGATOR/EUROPE-UK/"
    found = []
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            t = a.get_text(strip=True)
            if any(k in t.lower() for k in ["first officer", "f/o", "pilot", "low hour"]):
                trash = ["add pilot", "training", "resume", "cv", "interview", "help", "post", "advertise", "payscale", "roadshows"]
                if not any(tr in t.lower() for tr in trash) and len(t) > 10:
                    link = a['href'] if a['href'].startswith('http') else f"https://pilotcareercenter.com{a['href']}"
                    found.append(JobOffer(t, link, "Europe", "PCC"))
    except Exception as e:
        print(f"Erreur PCC: {e}")
    return found


def scan_platoon():
    """
    Platoon Aviation - aviation d'affaires, basée à Paris Le Bourget.
    Leur site est en React/JS pur. On tente plusieurs ATS connus.
    Si aucun ne répond, on scrape la page statique à la recherche de liens.
    """
    print("--- Scan Platoon Aviation ---")
    found = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    # Tentative 1 : BambooHR (même stack que Jetfly)
    try:
        r = requests.get("https://platoon-aviation.bamboohr.com/careers/list", headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json().get('result', [])
            for j in jobs:
                title = j.get('jobOpeningName', '')
                if any(k in title.lower() for k in ["pilot", "captain", "first officer", "f/o"]):
                    raw_loc = j.get('location', {})
                    loc = extract_location_from_title(title) or (
                        raw_loc.get('city') if isinstance(raw_loc, dict) else raw_loc
                    ) or "Le Bourget"
                    found.append(JobOffer(title, f"https://platoon-aviation.bamboohr.com/careers/{j.get('id')}", loc, "Platoon Aviation"))
            if found:
                return found
    except Exception:
        pass

    # Tentative 2 : Workable
    try:
        r = requests.get("https://apply.workable.com/api/v3/accounts/platoon-aviation/jobs/", headers=headers, timeout=10)
        if r.status_code == 200:
            for j in r.json().get('results', []):
                title = j.get('title', '')
                if any(k in title.lower() for k in ["pilot", "captain", "first officer"]):
                    loc = j.get('location', {}).get('city', 'Le Bourget') or 'Le Bourget'
                    link = f"https://apply.workable.com/platoon-aviation/j/{j.get('shortcode')}/"
                    found.append(JobOffer(title, link, loc, "Platoon Aviation"))
            if found:
                return found
    except Exception:
        pass

    # Tentative 3 : scrape page statique (peut retourner le shell JS uniquement)
    try:
        r = requests.get("https://www.flyplatoon.com/career", headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text().lower()
            if any(k in page_text for k in ["no position", "no opening", "pas de poste", "aucune offre"]):
                return [JobOffer("Aucune offre disponible", "https://www.flyplatoon.com/career", "Le Bourget", "Platoon Aviation", status="full")]
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                if any(k in text.lower() for k in ["pilot", "captain", "first officer", "commandant"]):
                    link = a['href'] if a['href'].startswith('http') else f"https://www.flyplatoon.com{a['href']}"
                    found.append(JobOffer(text, link, "Le Bourget", "Platoon Aviation"))
    except Exception as e:
        print(f"Erreur Platoon: {e}")

    return found


def scan_luxaviation():
    """
    Luxaviation Group - plus grand opérateur européen de jets privés (Luxembourg).
    Leur page carrières est un WordPress avec les offres chargées dynamiquement
    via un ATS externe. On scrape leur page principale pour trouver les liens.
    """
    print("--- Scan Luxaviation ---")
    url = "https://www.luxaviation.com/careers/"
    found = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            page_text = soup.get_text().lower()

            # Chercher des liens vers des offres pilotes dans la page
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                href = a['href'].lower()
                if any(k in text.lower() or k in href for k in ["pilot", "captain", "first officer", "commandant", "f/o"]):
                    exclusions = ["pilot training", "pilot program", "pilot course", "cadet"]
                    if not any(ex in text.lower() for ex in exclusions) and len(text) > 5:
                        link = a['href'] if a['href'].startswith('http') else f"https://www.luxaviation.com{a['href']}"
                        loc = extract_location_from_title(text) or "Luxembourg"
                        found.append(JobOffer(text, link, loc, "Luxaviation"))

            # Pas d'offres trouvées sur la page
            if not found:
                # Vérifier si la page mentionne explicitement l'absence de postes
                if any(k in page_text for k in ["no vacancies", "no current openings", "aucun poste"]):
                    return [JobOffer("Aucune offre disponible", url, "Luxembourg", "Luxaviation", status="full")]
                # Sinon : candidature spontanée possible
                return [JobOffer("Consulter les offres sur le site", url, "Luxembourg", "Luxaviation")]

    except Exception as e:
        print(f"Erreur Luxaviation: {e}")

    return found


def scan_la_compagnie():
    """
    La Compagnie - 100% Business Class Paris/Nice → New York.
    WeRecruit ne retourne pas les offres en HTML statique sur la page /offers
    (rendu JS), mais la page candidature spontanée contient une section
    "Nos dernières offres" en HTML pur avec tous les postes actifs.
    On scrape cette page et on filtre les postes PNT.
    """
    print("--- Scan La Compagnie ---")
    # Cette URL rend les offres en HTML statique (pas de JS requis)
    url = "https://careers.werecruit.io/fr/la-compagnie/offres/candidature-spontanee-46d497"
    base = "https://careers.werecruit.io"
    found = []
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # Les offres sont dans des <a> contenant un <h3> avec le titre
            for a in soup.find_all('a', href=True):
                h3 = a.find('h3')
                if not h3:
                    continue
                title = h3.get_text(strip=True)
                # Filtre PNT
                if not any(k in title.lower() for k in ["pilote", "pilot", "captain", "commandant", "first officer", "f/o", "pnt", "copilote"]):
                    continue
                link = a['href'] if a['href'].startswith('http') else base + a['href']
                # Localisation depuis les <li> de la card (contrat, rythme, ville)
                items = [li.get_text(strip=True) for li in a.find_all('li')]
                # La ville est généralement le dernier élément
                loc = items[-1] if items else "Paris"
                found.append(JobOffer(title, link, loc, "La Compagnie"))

            if not found:
                # Aucune offre PNT en ce moment, mais la compagnie est active
                return [JobOffer("Aucune offre PNT disponible", url, "Paris", "La Compagnie", status="full")]
    except Exception as e:
        print(f"Erreur La Compagnie: {e}")
    return found

# --- DISCORD ---
def send_to_discord(all_jobs):
    now = datetime.now()
    next_scan = now + timedelta(hours=CHECK_INTERVAL_HOURS)
    active = [j for j in all_jobs if j.status == "active"]
    full = [j for j in all_jobs if j.status == "full"]

    by_source = {}
    for j in all_jobs:
        by_source.setdefault(j.source, []).append(j)

    embeds = []
    for source, jobs in by_source.items():
        if jobs[0].status == "full":
            embeds.append({"title": f"🏢 {source.upper()}", "color": 0x2f3136,
                           "description": "🔴 **Effectifs complets.**"})
        else:
            fields = [{"name": f"✅ {j.title}", "value": f"📍 {j.location}\n[Voir l'offre]({j.link})", "inline": False}
                      for j in jobs]
            embeds.append({"title": f"🏢 {source.upper()}", "color": 0xf5a623, "fields": fields[:25]})

    payload = {
        "username": "Aero Job Monitor",
        "content": f"📝 **VEILLE AÉRONAUTIQUE — {now.strftime('%d/%m/%Y %H:%M')}**\n"
                   f"✅ {len(active)} offre(s) active(s) | 🔴 {len(full)} compagnie(s) complète(s)\n"
                   f"📅 Prochain scan : {next_scan.strftime('%d/%m/%Y %H:%M')}",
        "embeds": embeds[:10]
    }
    if not DISCORD_WEBHOOK_URL:
        print("⚠️  Discord ignoré : DISCORD_WEBHOOK_URL non défini.")
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print("✅ Discord notifié")
    except Exception as e:
        print(f"❌ Erreur Discord: {e}")

# --- SCAN ENGINE ---
def run_scan(notify_discord: bool = False):
    if _store["scan_running"]:
        print("Scan déjà en cours, skip.")
        return
    _store["scan_running"] = True
    print(f"\n=== SCAN LANCÉ {datetime.now().strftime('%d/%m/%Y %H:%M')} (Discord: {notify_discord}) ===")
    try:
        all_jobs = []
        all_jobs += scan_jetfly()
        all_jobs += scan_oyonnair()
        all_jobs += scan_pan_european()
        all_jobs += scan_clair_group()
        all_jobs += scan_chalair()
        all_jobs += scan_netjets()
        all_jobs += scan_platoon()
        all_jobs += scan_luxaviation()
        all_jobs += scan_la_compagnie()
        all_jobs += scan_pcc()
        _store["jobs"] = all_jobs
        _store["last_scan"] = datetime.now().isoformat()
        _store["next_scan"] = (datetime.now() + timedelta(hours=CHECK_INTERVAL_HOURS)).isoformat()
        if notify_discord:
            send_to_discord(all_jobs)
        else:
            print("ℹ️  Notification Discord ignorée (scan manuel ou démarrage)")
        save_data()
        print(f"=== SCAN TERMINÉ — {len(all_jobs)} offres ===")
    finally:
        _store["scan_running"] = False

# --- API ENDPOINTS ---
@app.get("/api/jobs")
def get_jobs(source: str = None, status: str = None, q: str = None):
    jobs = _store["jobs"]
    if source:
        jobs = [j for j in jobs if j.source.lower() == source.lower()]
    if status:
        jobs = [j for j in jobs if j.status == status]
    if q:
        q_low = q.lower()
        jobs = [j for j in jobs if q_low in j.title.lower() or q_low in j.location.lower()]
    return {
        "jobs": [j.__dict__ for j in jobs],
        "total": len(jobs),
        "last_scan": _store["last_scan"],
        "next_scan": _store["next_scan"],
        "scan_running": _store["scan_running"],
    }

@app.get("/api/sources")
def get_sources():
    sources = list(set(j.source for j in _store["jobs"]))
    return {"sources": sorted(sources)}

@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    if _store["scan_running"]:
        return {"message": "Scan déjà en cours", "status": "running"}
    background_tasks.add_task(run_scan, False)
    return {"message": "Scan lancé", "status": "started"}

@app.get("/api/status")
def get_status():
    active = sum(1 for j in _store["jobs"] if j.status == "active")
    full = sum(1 for j in _store["jobs"] if j.status == "full")
    return {
        "total": len(_store["jobs"]),
        "active": active,
        "full_companies": full,
        "last_scan": _store["last_scan"],
        "next_scan": _store["next_scan"],
        "scan_running": _store["scan_running"],
    }

@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html") as f:
        return f.read()

# --- STARTUP ---
@app.on_event("startup")
def startup():
    load_data()
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: run_scan(notify_discord=True), 'interval', hours=CHECK_INTERVAL_HOURS, id='auto_scan')
    scheduler.start()
    # Premier scan au démarrage si pas de données
    if not _store["jobs"]:
        t = threading.Thread(target=run_scan, kwargs={'notify_discord': False})
        t.daemon = True
        t.start()