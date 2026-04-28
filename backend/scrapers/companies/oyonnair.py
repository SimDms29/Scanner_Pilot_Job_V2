"""
Oyonnair — WordPress HTML statique.
Pas d'ATS. Surveille la page texte pour détecter une ouverture de recrutement.
"""
import logging
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://www.oyonnair.com/compagnie-aerienne/recrutement/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PILOT_KW  = {"pilote", "pnt", "commandant", "capitaine", "captain"}
FULL_KW   = {"effectifs sont complets", "effectifs complets", "pas de recrutement"}
EXCL_KW   = {"régulièrement", "rejoignez-nous", "recrutement", "domaines", "tels que"}


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        page_text = soup.get_text().lower()

        if any(k in page_text for k in FULL_KW):
            lat, lon = get_coords("Lyon")
            return [JobOffer(
                id=job_hash("Effectifs complets", URL),
                title="Effectifs complets",
                link=URL,
                source="Oyonnair",
                location="Lyon",
                status="full",
                lat=lat, lon=lon,
            )]

        for elem in soup.find_all(["h2", "h3", "a"]):
            text = elem.get_text(strip=True)
            if not any(k in text.lower() for k in PILOT_KW):
                continue
            if any(ex in text.lower() for ex in EXCL_KW) or len(text) > 100:
                continue
            link = URL
            if elem.name == "a" and elem.has_attr("href") and "recrutement" not in elem["href"]:
                link = elem["href"] if elem["href"].startswith("http") else "https://www.oyonnair.com" + elem["href"]
            lat, lon = get_coords("Lyon")
            found.append(JobOffer(
                id=job_hash(text, link),
                title=text.capitalize(),
                link=link,
                source="Oyonnair",
                location="Lyon",
                lat=lat, lon=lon,
            ))

        seen = set()
        found = [j for j in found if j.title not in seen and not seen.add(j.title)]
        log.info(f"Oyonnair: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Oyonnair: {e}")
        return None
    return found
