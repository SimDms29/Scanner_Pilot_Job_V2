"""
Gama Aviation — Opérateur bizjet/hélico UK (Luton, Glasgow…).
Salesforce Recruit : même portail que Loganair, colonnes différentes.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

BASE = "https://gama-aviation.my.salesforce-sites.com"
URL  = f"{BASE}/Recruit/fRecruit__ApplyJobList?portal=Myairops+Portal"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|second officers?|commanders?|copilots?|co-pilots?|f/o|flight crew|flight deck)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|mechanic|manager|director|recruiter|trainer|instructor)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for tr in soup.find_all("tr"):
            cells = tr.find_all("td")
            if len(cells) < 5:
                continue
            a = tr.find("a", href=True)
            if not a or "ApplyJob" not in a["href"] or "ApplyJobList" in a["href"]:
                continue

            title    = cells[0].get_text(strip=True)
            raw_loc  = cells[4].get_text(strip=True)
            # Strip hangar/building suffixes that confuse the geocoder
            location = re.sub(r'\s+(hangar|building|unit|gate)\s*\d*$', '', raw_loc, flags=re.I).strip() or "United Kingdom"
            href     = a["href"]

            if not title or href in seen:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            seen.add(href)
            link = BASE + href if href.startswith("/") else href
            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Gama Aviation",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"Gama Aviation: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Gama Aviation: {e}")
        return None
    return found
