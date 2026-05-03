"""
Spreeflug — Opérateur bizjet allemand (Phenom 300, C525), Berlin.
WordPress SiteOrigin accordion : titres dans class sow-accordion-title.
Pas de liens individuels, lien fixe vers la page carrières.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://www.spreeflug.de/en/career-jobs/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|commanders?|copilots?|f/o|flight crew|flight deck)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|manager|director|dispatch|sales|administrative|commercial)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for el in soup.find_all(class_="sow-accordion-title"):
            title = el.get_text(strip=True)
            if not title:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            lat, lon = get_coords("Berlin")
            found.append(JobOffer(
                id=job_hash(title, URL),
                title=title,
                link=URL,
                source="Spreeflug",
                location="Berlin",
                lat=lat, lon=lon,
            ))

        log.info(f"Spreeflug: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Spreeflug: {e}")
        return None
    return found
