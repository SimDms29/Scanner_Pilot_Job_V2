"""
Danish Air Transport (DAT) — Compagnie régionale danoise (ATR-72, A320).
Les offres sont listées sur /en/corporate/careers/ comme pages individuelles WordPress.
Titres extraits du h2/h3 dans le bloc de chaque offre.
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

CAREERS_URL = "https://dat.dk/en/corporate/careers/"
HEADERS     = {"User-Agent": "Mozilla/5.0"}
CAREER_RE   = re.compile(r'/en/corporate/careers/[^/]+/$')
PILOT_RE    = re.compile(r'\b(pilots?|captains?|first officers?|commanders?|copilots?|f/o|flight crew|pnt|cps?|fos?)\b', re.I)
EXCLUDE_RE  = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|technician|sales|mcc|manager|chief pilot)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(CAREERS_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not CAREER_RE.search(href):
                continue
            # Normalise URL
            if not href.startswith("http"):
                href = "https://dat.dk" + href
            if href in seen or href.rstrip("/") == CAREERS_URL.rstrip("/"):
                continue
            seen.add(href)

            # Extract title from the nearest heading in the surrounding block
            title = None
            parent = a.parent
            for _ in range(6):
                heading = parent.find(["h2", "h3", "h4", "h1"])
                if heading:
                    title = heading.get_text(strip=True)
                    break
                if parent.parent is None:
                    break
                parent = parent.parent

            if not title:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            lat, lon = get_coords("Copenhagen")
            found.append(JobOffer(
                id=job_hash(title, href),
                title=title,
                link=href,
                source="Danish Air Transport",
                location="Copenhagen",
                lat=lat, lon=lon,
            ))

        log.info(f"Danish Air Transport: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Danish Air Transport: {e}")
        return None
    return found
