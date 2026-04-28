"""
Pan Européenne Air Service — site statique, pas d'ATS.
Surveille la page pour détecter l'ouverture d'un recrutement pilote.
Email de contact : peas.jobs@gmail.com
"""
import logging
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://www.paneuropeenne.com/en/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PILOT_KW = {"pilot", "captain", "first officer", "f/o", "pnt"}
FULL_KW  = {"no employment at the moment", "no employment", "no vacancy"}


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        page_text = soup.get_text().lower()
        lat, lon = get_coords("Chambéry")

        if any(k in page_text for k in FULL_KW):
            return [JobOffer(
                id=job_hash("Effectifs complets", URL),
                title="Effectifs complets",
                link=URL,
                source="Pan Européenne",
                location="Chambéry",
                status="full",
                lat=lat, lon=lon,
            )]

        for elem in soup.find_all(["h2", "h3", "h4", "p", "li", "a"]):
            text = elem.get_text(strip=True)
            if not any(k in text.lower() for k in PILOT_KW):
                continue
            if len(text) < 10 or len(text) > 200:
                continue
            link = URL
            if elem.name == "a" and elem.has_attr("href"):
                link = elem["href"] if elem["href"].startswith("http") else "https://www.paneuropeenne.com" + elem["href"]
            found.append(JobOffer(
                id=job_hash(text, link),
                title=text.capitalize(),
                link=link,
                source="Pan Européenne",
                location="Chambéry",
                lat=lat, lon=lon,
            ))

        seen = set()
        found = [j for j in found if j.title not in seen and not seen.add(j.title)]
        log.info(f"Pan Européenne: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Pan Européenne: {e}")
        return None
    return found
