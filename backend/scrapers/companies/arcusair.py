"""
Arcus Air — Opérateur bizjet allemand (Phenom 100/300, ERJ-145), Zweibrücken.
HubSpot custom portal : postes listés sur /en/careers-at-arcus-air avec liens
vers /en/open-position-{slug}. Le texte du lien est le titre du poste.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://arcus-air.com/en/careers-at-arcus-air"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|second officers?|commanders?|copilots?|f/o|flight crew|flight deck)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|manager|director|dispatcher|sales|operations manager)\b', re.I)
JOB_RE     = re.compile(r'/en/open-position-', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=JOB_RE):
            href  = a["href"].split("?")[0]
            title = a.get_text(strip=True)
            if not title or href in seen:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            seen.add(href)
            link = href if href.startswith("http") else f"https://arcus-air.com{href}"
            lat, lon = get_coords("Zweibrücken")
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Arcus Air",
                location="Zweibrücken",
                lat=lat, lon=lon,
            ))

        log.info(f"Arcus Air: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Arcus Air: {e}")
        return None
    return found
