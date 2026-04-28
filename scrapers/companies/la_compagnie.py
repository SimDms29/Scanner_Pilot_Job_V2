"""
La Compagnie — WeRecruit (HTML statique).
La page candidature spontanée liste toutes les offres actives en HTML pur.
"""
import logging
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL  = "https://careers.werecruit.io/fr/la-compagnie/offres/candidature-spontanee-46d497"
BASE = "https://careers.werecruit.io"
PILOT_KW = {"pilote", "pilot", "captain", "commandant", "first officer", "f/o", "pnt", "copilote"}


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            h3 = a.find("h3")
            if not h3:
                continue
            title = h3.get_text(strip=True)
            if not any(k in title.lower() for k in PILOT_KW):
                continue
            link = a["href"] if a["href"].startswith("http") else BASE + a["href"]
            items = [li.get_text(strip=True) for li in a.find_all("li")]
            loc = items[-1] if items else "Paris"
            lat, lon = get_coords(loc)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="La Compagnie",
                location=loc,
                lat=lat,
                lon=lon,
            ))
        log.info(f"La Compagnie: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur La Compagnie: {e}")
        return None
    return found
