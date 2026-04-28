"""
Chalair Aviation — WordPress HTML statique.
Les offres PNT sont listées directement dans le DOM.
"""
import logging
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://www.chalair.fr/offres-emplois"
BASE    = "https://www.chalair.fr"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PILOT_KW    = {"pnt", "pilote", "captain", "commandant"}
EXCLUDE_KW  = {"candidature spontanée", "candidature-spontanée"}


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"].lower()
            if not any(k in text.lower() or k in href for k in PILOT_KW):
                continue
            if any(k in text.lower() or k in href for k in EXCLUDE_KW):
                continue
            link = a["href"] if a["href"].startswith("http") else BASE + a["href"]
            if link in seen or len(text) < 5:
                continue
            seen.add(link)
            lat, lon = get_coords("France")
            found.append(JobOffer(
                id=job_hash(text or "Candidature PNT", link),
                title=text or "Candidature PNT",
                link=link,
                source="Chalair",
                location="France",
                lat=lat,
                lon=lon,
            ))
        log.info(f"Chalair: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Chalair: {e}")
        return None
    return found
