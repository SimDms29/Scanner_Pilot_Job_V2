"""
DAS Private Jets — Opérateur bizjet allemand (Phenom 300), Mengen (Baden-Württemberg).
Site custom WordPress : offres sur /career, liens vers /karriere/{slug}.
Ville extraite du container (code postal + nom).
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

URL     = "https://www.das-private-jets.com/career"
HEADERS = {"User-Agent": "Mozilla/5.0"}

PILOT_RE   = re.compile(r'\b(pilots?|captains?|kapit[äa]ns?|first officers?|copilots?|kopilots?|f/o|flight crew|phenom|embraer|emb\d)\b', re.I)
EXCLUDE_RE = re.compile(r'\b(sales|verkauf|studium|ausbildung|kaufmann|kauffrau|b[üu]ro|management|operations manager|dispatch)\b', re.I)
PLZ_RE     = re.compile(r'\b(\d{5})\s+([A-Za-zÄÖÜäöüß\-]+)')


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/karriere/" not in href:
                continue
            if href in seen:
                continue

            title = a.get_text(strip=True)
            if not title:
                continue
            if not PILOT_RE.search(title):
                continue
            if EXCLUDE_RE.search(title):
                continue

            seen.add(href)

            # Extract city from parent container
            container = a.find_parent(["div", "li", "article", "section"])
            location = "Germany"
            if container:
                text = container.get_text(separator=" ", strip=True)
                m = PLZ_RE.search(text)
                if m:
                    location = m.group(2)

            link = href if href.startswith("http") else f"https://www.das-private-jets.com{href}"
            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, link),
                title=title,
                link=link,
                source="DAS Private Jets",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"DAS Private Jets: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur DAS Private Jets: {e}")
        return None
    return found
