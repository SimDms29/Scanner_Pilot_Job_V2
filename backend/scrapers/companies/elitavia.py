"""
Elit'Avia — WordPress + Elementor. Les offres sont sur /careers/ sous forme
de liens /job-post-{slug}/. Le titre et la localisation se trouvent sur chaque
page individuelle (h1 + première ligne de localisation).
"""
import logging
import re
import requests
from bs4 import BeautifulSoup
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

CAREERS_URL = "https://elitavia.com/careers/"
HEADERS     = {"User-Agent": "Mozilla/5.0"}
PILOT_RE    = re.compile(r'\b(pilot|captain|first officer|commander|copilot|f/o|flight crew|pnt)\b', re.I)
EXCLUDE_RE  = re.compile(r'\b(cabin|attendant|steward|maintenance|head of|travel|operations officer|nominated person)\b', re.I)


def _fetch_job(url: str) -> tuple[str, str]:
    """Return (title, location) from individual job post page."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        title = ""
        location = "Europe"

        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
            title = re.sub(r'^job post\s+', '', title, flags=re.I)

        # La localisation apparaît souvent comme une courte ligne isolée
        # après le titre, avant le corps du texte
        for el in soup.find_all(["p", "div", "span"]):
            text = el.get_text(strip=True)
            if 3 < len(text) < 35 and text[0].isupper() and not any(
                k in text.lower() for k in ["elitavia", "career", "skip", "aircraft",
                                             "charter", "management", "sustainability",
                                             "first officer", "captain", "pilot", "crew"]
            ) and not text.startswith("http"):
                location = text
                break

        return title, location
    except Exception:
        return "", "Europe"


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    seen: set[str] = set()
    try:
        r = requests.get(CAREERS_URL, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "job-post" not in href or href in seen:
                continue
            seen.add(href)

            # Filtre rapide sur le slug avant de fetcher la page
            slug = href.rstrip("/").split("/")[-1]
            slug_text = re.sub(r'^job-post-', '', slug).replace("-", " ")
            if not PILOT_RE.search(slug_text):
                continue
            if EXCLUDE_RE.search(slug_text):
                continue

            title, location = _fetch_job(href)
            if not title:
                title = slug_text.title()
            if not PILOT_RE.search(title) or EXCLUDE_RE.search(title):
                continue

            lat, lon = get_coords(location)
            found.append(JobOffer(
                id=job_hash(title, href),
                title=title,
                link=href,
                source="Elit'Avia",
                location=location,
                lat=lat, lon=lon,
            ))

        log.info(f"Elit'Avia: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Elit'Avia: {e}")
        return None
    return found
