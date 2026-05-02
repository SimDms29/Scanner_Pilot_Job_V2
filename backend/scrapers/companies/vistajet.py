"""
VistaJet — iCIMS hub Vista Global, catégorie Flight Deck (8723).
L'URL avec in_iframe=1 retourne le HTML statique avec tous les jobs.
Filtre sur Company != Vista America pour garder uniquement les postes EU/global.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL = (
    "https://hub-vistaglobal.icims.com/jobs/search"
    "?ss=1&searchCategory=8723&mobile=false&width=1296&height=500"
    "&bga=true&needsRedirect=false&jan1offset=60&jun1offset=120&in_iframe=1"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://hub-vistaglobal.icims.com/",
}
PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|second officers?|commanders?|copilots?|f/o|flight crew|flight deck|tri|tre|type rating)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|manager|director|recruiter|host)\b', re.I)
US_COMPANIES = {"vista america", "xo", "xojet"}
US_LOCATIONS = {"united states", "columbus", "teterboro", "bay city", "bridgeport", "van nuys"}


def _field(group, field_name: str) -> str:
    """Extract a field value from an iCIMS_JobHeaderGroup div."""
    for tag in group.find_all(class_="iCIMS_JobHeaderTag"):
        field = tag.find(class_="iCIMS_JobHeaderField")
        data  = tag.find(class_="iCIMS_JobHeaderData")
        if field and data and field.get_text(strip=True) == field_name:
            return data.get_text(strip=True)
    return ""


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for card in soup.find_all(class_="iCIMS_JobCardItem"):
            # Titre : premier lien, préfixé par "Title" à stripper
            a = card.find("a", href=True)
            if not a:
                continue
            title = re.sub(r"^Title", "", a.get_text(strip=True)).strip()
            href  = a["href"]
            if not title or href in seen:
                continue

            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            group = card.find(class_="iCIMS_JobHeaderGroup")
            if not group:
                continue

            company  = _field(group, "Company").lower()
            location = _field(group, "Job Location") or "Europe"

            # Exclure les postes US
            if any(us in company for us in US_COMPANIES):
                continue
            if location.lower() in US_LOCATIONS:
                continue

            # "European Union" → coordonnées Europe centrale
            geo_loc = "Malta" if "Malta" in location else location
            seen.add(href)
            link = href if href.startswith("http") else f"https://hub-vistaglobal.icims.com{href}"

            lat, lon = get_coords(geo_loc)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="VistaJet",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"VistaJet: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur VistaJet: {e}")
        return None
    return found
