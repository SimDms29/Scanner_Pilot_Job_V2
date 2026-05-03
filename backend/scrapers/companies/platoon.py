"""
Platoon Aviation — Opérateur bizjet PC-24 basé à Hamburg.
Personio ATS : feed XML public à /xml, pas d'auth requise.
"""
import logging
import re
import requests
from xml.etree import ElementTree as ET
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

XML_URL  = "https://platoon-aviation.jobs.personio.de/xml"
BASE_URL = "https://platoon-aviation.jobs.personio.de/job/{job_id}"
HEADERS  = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|second officers?|commanders?|copilots?|f/o|flight crew|flight deck|ab.initio)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|maintenance|engineer|dispatcher|recruiter|sales|manager|controller|head of|CAMO)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(XML_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        for pos in root.findall("position"):
            title  = (pos.findtext("name") or "").strip()
            job_id = pos.findtext("id") or ""
            office = pos.findtext("office") or "Hamburg"

            if not title or not job_id:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            link = BASE_URL.format(job_id=job_id)
            lat, lon = get_coords(office)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Platoon Aviation",
                location=office,
                lat=lat, lon=lon,
            ))

        log.info(f"Platoon Aviation: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Platoon Aviation: {e}")
        return None
    return found
