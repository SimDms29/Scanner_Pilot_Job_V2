"""
Helvetic Airways — portail custom career.helvetic.com (Apache Wicket).
Surveille la page /flightcrew : les postes ouverts apparaissent comme
liens de navigation avec ancres (#id) pointant vers des sections de détail.
"""
import logging
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://career.helvetic.com/flightcrew"
BASE    = "https://career.helvetic.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PILOT_RE_WORDS = {"pilot", "captain", "first officer", "commander", "copilot", "f/o", "pnt", "crew"}
EXCLUDE_WORDS  = {"cabin", "attendant", "steward", "maintenance", "backoffice", "cadet"}


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Pas d'offres en ce moment — signal explicite
        if "keine offenen stellen" in soup.get_text().lower():
            log.info("Helvetic: aucun poste flight crew en ce moment")
            return []

        # Parser les liens de navigation vers les sections de postes
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("#") or len(href) < 3:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 4:
                continue

            title_low = title.lower()
            if any(w in title_low for w in EXCLUDE_WORDS):
                continue
            if not any(w in title_low for w in PILOT_RE_WORDS):
                # accepter si la section contient des mots pilote
                section = soup.find(id=href.lstrip("#"))
                if not section or not any(w in section.get_text().lower() for w in PILOT_RE_WORDS):
                    continue

            if title in seen:
                continue
            seen.add(title)

            link = f"{BASE}/flightcrew{href}"
            lat, lon = get_coords("Zurich")
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Helvetic Airways",
                location="Zurich",
                lat=lat,
                lon=lon,
            ))

        log.info(f"Helvetic: {len(found)} offre(s) flight crew")
    except Exception as e:
        log.error(f"Erreur Helvetic: {e}")
        return None
    return found
