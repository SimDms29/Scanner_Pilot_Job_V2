"""
NetJets Europe — SAP SuccessFactors (HTML scraping).
Search endpoint: netjets.jobs.hr.cloud.sap
"""
import logging
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

SEARCH_URL = "https://netjets.jobs.hr.cloud.sap/europe/search/?createNewAlert=false&q=pilot"
BASE_URL   = "https://careers.netjets.com"
HEADERS    = {"User-Agent": "Mozilla/5.0"}
PILOT_KW   = {"pilot", "captain", "first officer", "second in command", "f/o", "pic", "sic"}


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        r = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.find_all("tr"):
            link_tag = row.find("a", href=True)
            if not link_tag:
                continue
            title = link_tag.get_text(strip=True)
            if not any(k in title.lower() for k in PILOT_KW):
                continue
            href = link_tag["href"]
            if not href.startswith("http"):
                href = BASE_URL + href
            cells = row.find_all("td")
            location = cells[1].get_text(strip=True) if len(cells) >= 2 else "N/C"
            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, href),
                title=title,
                link=href,
                source="NetJets Europe",
                location=location,
                lat=lat,
                lon=lon,
            ))
        log.info(f"NetJets: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur NetJets: {e}")
        return None
    return found
