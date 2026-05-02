"""
Loganair — Compagnie régionale écossaise (ATR-72, Twin Otter, Saab 340...).
Portail Salesforce Recruit : HTML statique, tous les jobs visibles en page 1.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

BASE    = "https://loganair.my.salesforce-sites.com"
URL     = f"{BASE}/recruit/fRecruit__ApplyJobList"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|commanders?|copilots?|f/o|flight crew|flight deck|cps?|fos?)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|finance|sales|account|manager|head of)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "ApplyJob" not in href or "ApplyJobList" in href:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            link = BASE + href if href.startswith("/") else href
            if link in seen:
                continue
            seen.add(link)

            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            # Location from the table row (3rd td after the job title link)
            location = "United Kingdom"
            row = a.find_parent("tr")
            if row:
                cells = row.find_all("td")
                if len(cells) >= 3:
                    loc = cells[2].get_text(strip=True)
                    if loc and len(loc) > 1:
                        location = loc

            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Loganair",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"Loganair: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Loganair: {e}")
        return None
    return found
