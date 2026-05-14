"""
GlobalJet — Opérateur VVIP Luxembourg (G650, Falcon, PC24, A320ACJ, Global).
Site Drupal avec Views AJAX : jobs rendus côté client → Playwright requis.
URL hash générée par slugification du titre (confirmée par inspection DOM).
"""
import logging
import os
import re
from playwright.sync_api import sync_playwright
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

BASE_URL = "https://globaljet.aero/en/careers"

PILOT_RE = re.compile(
    r'\b(pilots?|captains?|first officers?|f/o|copilots?|flight crew|'
    r'g650|g550|g7500|global\s*6000|falcon|pc-?24|a320|acj|embraer)\b',
    re.I
)
EXCLUDE_RE = re.compile(r'\b(attendant|steward|dispatcher|engineer|accountant|reservation|purchasing|coordinator|management|support)\b', re.I)

# Cities that may appear in job titles to refine "WORLDWIDE" location
CITY_RE = re.compile(
    r'\b(Nice|Marseille|Geneva|Genève|Luxembourg|Paris|London|Zurich|Zürich|Monaco|Dubai|Dubaï)\b',
    re.I
)


def _slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s.strip())
    return s


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        with sync_playwright() as p:
            exe = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
            browser = p.chromium.launch(headless=True, **({"executable_path": exe} if exe else {}))
            page = browser.new_page()
            page.goto(BASE_URL, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_selector('.vacancies__item', timeout=15000)
            page.wait_for_timeout(1500)

            # Remove cookie consent overlay if present
            page.evaluate(
                'document.getElementById("CybotCookiebotDialog")?.remove();'
                'document.getElementById("CybotCookiebotDialogBodyUnderlay")?.remove()'
            )

            items = page.query_selector_all('.vacancies__item')
            for item in items:
                title_el = item.query_selector('div.text p')
                loc_el = item.query_selector('.vacancies__city p')
                if not title_el:
                    continue

                title = title_el.inner_text().strip()
                raw_loc = loc_el.inner_text().strip() if loc_el else ''

                if not PILOT_RE.search(title):
                    continue
                if EXCLUDE_RE.search(title):
                    continue

                # Resolve location: element value if specific, else extract from title, else HQ
                if raw_loc and raw_loc.upper() not in ('', 'WORLDWIDE'):
                    location = raw_loc.title()
                else:
                    m = CITY_RE.search(title)
                    location = m.group(1) if m else 'Luxembourg'

                link = f"{BASE_URL}#{_slugify(title)}"
                lat, lon = get_coords(location)
                found.append(JobOffer(
                    id=job_hash(title, link),
                    title=title,
                    link=link,
                    source='GlobalJet',
                    location=location,
                    lat=lat, lon=lon,
                ))

            browser.close()

        log.info(f"GlobalJet: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur GlobalJet: {e}")
        return None
    return found
