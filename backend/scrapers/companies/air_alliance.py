"""
Air Alliance Gruppe — Opérateur allemand de vols ambulance + charter.
Portail custom career.air-alliance.de, jobs listés sur /en avec ?id= params.
Recrute des pilotes "Ready Entry" sur PC-12, PC-24, Learjet 45.
"""
import logging
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

BASE    = "https://career.air-alliance.de"
URL     = f"{BASE}/en"
HEADERS = {"User-Agent": "Mozilla/5.0"}
PILOT_RE   = re.compile(r'\b(pilot|captain|first officer|commander|copilot|f/o|flight crew|pnt|kapitän)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|technician|mechanic|arzt|medizin|ärztin|elektroniker|mechaniker|compliance|initiativ)\b', re.I)
ZIP_RE  = re.compile(r'^\d{4,6}\s+')


def _city_from_maps(href: str) -> str | None:
    """Extract city name from Google Maps search URL query string."""
    try:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        raw = query.get("query", [None])[0]
        if not raw:
            return None
        parts = raw.split(",")
        if len(parts) < 2:
            return None
        # second-to-last part is typically "ZIPCODE City"
        city_part = parts[-2].strip()
        city = ZIP_RE.sub("", city_part).strip()
        return city if city else None
    except Exception:
        return None


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not re.match(r"^/en\?id=", href):
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 10 or href in seen:
                continue
            seen.add(href)

            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            # Look for Google Maps location link within the job's own card (portlet)
            location = "Germany"
            for ancestor in a.parents:
                classes = ancestor.get("class", [])
                if "portlet" in classes:
                    maps = ancestor.find("a", href=lambda h: h and "maps/search" in h)
                    if maps:
                        city = _city_from_maps(maps["href"])
                        if city:
                            location = city
                    break
                if ancestor.name in ("body", "html", "main"):
                    break

            link = f"{BASE}{href}"
            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Air Alliance",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"Air Alliance: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Air Alliance: {e}")
        return None
    return found
