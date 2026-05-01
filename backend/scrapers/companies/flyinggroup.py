"""
Flying Group — Opérateur belge basé à Anvers.
WordPress REST API : catégorie 7 = "Job".
Pas de postes pilote actuellement, mais le scraper se déclenche dès ouverture.
"""
import logging
import re
import requests
from html import unescape
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

API_URL   = "https://www.flyinggroup.aero/wp-json/wp/v2/posts?categories=7&per_page=50&status=publish"
HEADERS   = {"User-Agent": "Mozilla/5.0"}
PILOT_RE  = re.compile(r'\b(pilot|captain|first officer|commander|copilot|f/o|flight crew|pnt)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|technician|fueler|desk|driver|chauffeur|occ|airworthiness|finance|sales|marketing|hr|accounting)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(API_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        posts = r.json()

        for post in posts:
            title = unescape(post.get("title", {}).get("rendered", "").strip())
            link  = post.get("link", "")
            if not title or not link:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            lat, lon = get_coords("Antwerp")
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Flying Group",
                location="Antwerp",
                lat=lat, lon=lon,
            ))

        log.info(f"Flying Group: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Flying Group: {e}")
        return None
    return found
