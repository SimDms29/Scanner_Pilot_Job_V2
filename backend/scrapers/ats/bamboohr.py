"""
Generic BambooHR scraper.
Usage: scan(company_slug, company_name, default_location)
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
EXCLUDE_RE = re.compile(
    r'\b(ground|dispatch|sales|accountant|mechanic|technician|instructor)\b',
    re.IGNORECASE,
)


def scan(company_slug: str, company_name: str, default_location: str) -> list[JobOffer] | None:
    url = f"https://{company_slug}.bamboohr.com/careers/list"
    found: list[JobOffer] = []
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        jobs = r.json().get("result", [])
        for j in jobs:
            title = j.get("jobOpeningName", "")
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue
            raw_loc = j.get("location", {})
            if isinstance(raw_loc, dict):
                loc = raw_loc.get("city") or default_location
            else:
                loc = raw_loc or default_location
            link = f"https://{company_slug}.bamboohr.com/careers/{j.get('id')}"
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
        log.info(f"BambooHR {company_name}: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur BambooHR {company_name}: {e}")
        return None
    return found
