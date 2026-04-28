"""
Generic Recruitee scraper.
Usage: scan(company_slug, company_name, default_location)
API: https://{slug}.recruitee.com/api/offers/
"""
import re
import logging
import requests
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

PILOT_RE = re.compile(
    r'\b(pilot|captain|first officer|commandant|copilot|copilote|pnt|f/o)\b',
    re.IGNORECASE,
)


def scan(company_slug: str, company_name: str, default_location: str) -> list[JobOffer] | None:
    url = f"https://{company_slug}.recruitee.com/api/offers/"
    found: list[JobOffer] = []
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        offers = r.json().get("offers", [])
        for o in offers:
            title = o.get("title", "")
            if not PILOT_RE.search(title):
                continue
            loc = o.get("city") or o.get("location") or default_location
            link = (
                o.get("careers_url")
                or f"https://{company_slug}.recruitee.com/o/{o.get('slug', '')}"
            )
            lat, lon = get_coords(loc)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source=company_name,
                location=loc,
                lat=lat,
                lon=lon,
            ))
        log.info(f"Recruitee {company_name}: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Recruitee {company_name}: {e}")
        return None
    return found
