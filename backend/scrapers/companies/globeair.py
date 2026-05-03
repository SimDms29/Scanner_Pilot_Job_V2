"""
GlobeAir — Opérateur bizjet européen (Citation M2/CJ), Linz (Autriche).
Portail custom globeair.com/career, liens vers /j/{id}.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://www.globeair.com/career"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|second officers?|commanders?|copilots?|f/o|flight crew|flight deck)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|manager|director|logistics|procurement|marketing|sales|accountant|buchhalter)\b', re.I)
JOB_RE     = re.compile(r'/j/\d+')


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for col in soup.find_all("div", class_="column"):
            if "is-6" not in col.get("class", []):
                continue
            a = col.find("a", href=JOB_RE)
            if not a:
                continue

            href  = a["href"]
            if href in seen:
                continue

            full_text = col.get_text(strip=True)
            title = re.sub(r"View opportunity.*$", "", full_text, flags=re.I).strip()
            if not title:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            seen.add(href)
            link = href if href.startswith("http") else f"https://www.globeair.com{href}"
            lat, lon = get_coords("Linz")
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="GlobeAir",
                location="Linz",
                lat=lat, lon=lon,
            ))

        log.info(f"GlobeAir: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur GlobeAir: {e}")
        return None
    return found
