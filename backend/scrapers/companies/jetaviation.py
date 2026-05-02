"""
Jet Aviation — Opérateur BizJet mondial, portail SAP SuccessFactors custom.
Page Europe statique sur jobs.jetaviation.com/go/Europe/8766702/.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://jobs.jetaviation.com/go/Europe/8766702/"
BASE    = "https://jobs.jetaviation.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|second officers?|commanders?|copilots?|f/o|flight crew|flight deck|pnt)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|intern|manager|director|recruiter)\b', re.I)
CITY_RE    = re.compile(r'^([^,]+)')


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for tr in soup.find_all("tr"):
            links = tr.find_all("a", href=True)
            if not links:
                continue
            title = links[0].get_text(strip=True)
            href  = links[0]["href"]
            if not title or not href or href in seen:
                continue

            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            seen.add(href)
            link = BASE + href if href.startswith("/") else href

            # Location : 2nd cell, format "City, CC, Country, ZIP"
            location = "Europe"
            cells = tr.find_all("td")
            if len(cells) > 1:
                raw = cells[1].get_text(strip=True)
                m = CITY_RE.match(raw)
                if m:
                    location = m.group(1).strip()

            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Jet Aviation",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"Jet Aviation: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Jet Aviation: {e}")
        return None
    return found
