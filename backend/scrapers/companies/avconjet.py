"""
Avcon Jet — WordPress custom (Vienna, Austria).
Les offres sont listées sur /career/ comme liens /job/{slug}/.
Candidature par email recruitment@avconjet.com.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

CAREERS_URL = "https://www.avconjet.at/career/"
HEADERS     = {"User-Agent": "Mozilla/5.0"}
PILOT_RE    = re.compile(r'\b(pilot|captain|first officer|commander|copilot|f/o|flight crew|pnt)\b', re.I)
EXCLUDE_RE  = re.compile(r'\b(cabin|attendant|maintenance|sales|finance|dispatch|controlling|manager|coordinator|specialist|lead)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(CAREERS_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/job/" not in href or href in seen:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue
            seen.add(href)
            lat, lon = get_coords("Vienna")
            found.append(JobOffer(
                id=job_hash(title, href),
                title=title,
                link=href,
                source="Avcon Jet",
                location="Vienna",
                lat=lat, lon=lon,
            ))

        log.info(f"Avcon Jet: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Avcon Jet: {e}")
        return None
    return found
