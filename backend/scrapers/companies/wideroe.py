"""
Widerøe — Compagnie régionale norvégienne (Q400, Twin Otter…).
Portail de recrutement jobbiwideroe.no → liens vers jobbnorge.no.
HTML statique, pas d'API publique JobbNorge.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://jobbiwideroe.no/ledige-stillinger/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|copilots?|f/o|flight crew|flight deck)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|manager|director|ekspedit|arbeider)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "jobbnorge.no" not in href:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 3 or href in seen:
                continue

            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            seen.add(href)
            lat, lon = get_coords("Norway")
            found.append(JobOffer(
                id=job_hash(title, href),
                title=title,
                link=href,
                source="Widerøe",
                location="Norway",
                lat=lat, lon=lon,
            ))

        log.info(f"Widerøe: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Widerøe: {e}")
        return None
    return found
