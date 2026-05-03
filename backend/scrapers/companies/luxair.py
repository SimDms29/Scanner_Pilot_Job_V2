"""
Luxair — Compagnie nationale luxembourgeoise (B737, Embraer E1/E2).
Cornerstone OnDemand (CSOD) : le token JWT est récupéré depuis la page career site,
puis on appelle l'API rec-job-search/external/jobs sur uk.api.csod.com.
"""
import logging
import re
import requests
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

CAREER_URL = "https://luxair.csod.com/ux/ats/careersite/27/home?c=luxair&lang=fr-FR"
API_URL    = "https://uk.api.csod.com/rec-job-search/external/jobs"
JOB_URL    = "https://luxair.csod.com/ux/ats/careersite/27/home?c=luxair&requisitionId={req_id}"
HEADERS    = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|first officers?|second officers?|commanders?|copilots?|f/o|flight crew|flight deck)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(cabin|attendant|steward|technician|mechanic|intern|stage|summer|apprenti)\b', re.I)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        # Session obligatoire : CSOD valide le token via le cookie BrowserId
        session = requests.Session()
        session.headers.update(HEADERS)

        r = session.get(CAREER_URL, timeout=15)
        r.raise_for_status()
        m = re.search(r'"token":"([^"]+)"', r.text)
        if not m:
            log.error("Luxair: impossible d'extraire le token CSOD")
            return None
        token = m.group(1)

        resp = session.post(
            API_URL,
            json={
                "careerSiteId": 27,
                "careerSitePageId": 27,
                "pageNumber": 1,
                "pageSize": 100,
                "cultureId": 13,
                "cultureName": "fr-FR",
                "searchText": "",
                "states": [],
                "countryCodes": [],
                "cities": [],
                "placeID": "",
                "radius": None,
                "selectedCustomCheckboxFilters": [],
                "selectedCustomDropDownFilters": [],
                "selectedCustomRadioFilters": [],
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        for req in data.get("data", {}).get("requisitions", []):
            title = req.get("displayJobTitle", "").strip()
            if not title:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            req_id = req["requisitionId"]
            link = JOB_URL.format(req_id=req_id)
            location = "Luxembourg"
            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="Luxair",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"Luxair: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Luxair: {e}")
        return None
    return found
