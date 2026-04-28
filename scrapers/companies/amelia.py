"""
Amelia — API custom : career.flyamelia.com/api/offers/
"""
import logging
import requests
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

API_URL = "https://career.flyamelia.com/api/offers/"
PILOT_KEYWORDS = {"pilot", "captain", "officier", "pnt", "commandant", "first officer", "copilot"}


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        offers = r.json().get("offers", [])
        for o in offers:
            title = o.get("title", "")
            if not any(k in title.lower() for k in PILOT_KEYWORDS):
                continue
            link = (
                o.get("careers_url")
                or f"https://career.flyamelia.com/o/{o.get('slug', '')}"
            )
            locations = o.get("locations", [])
            loc = locations[0].get("name", "France") if locations else o.get("location", "France")
            lat, lon = get_coords(loc)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Amelia",
                location=loc,
                lat=lat,
                lon=lon,
            ))
        if not found:
            log.info("Amelia: aucune offre PNT active")
        else:
            log.info(f"Amelia: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Amelia: {e}")
        return None
    return found
