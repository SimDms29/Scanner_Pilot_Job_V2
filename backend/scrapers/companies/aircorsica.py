"""
Air Corsica — Compagnie régionale Corse (A320, ATR).
Portail Salesforce Lightning (package crtarecr) — rendu JS pur → Playwright requis.
Les jobs s'affichent dans #JobOfferSearchContainer après initialisation du framework Lightning.
"""
import logging
import re
from playwright.sync_api import sync_playwright
from models import JobOffer
from storage import job_hash
from geocoder import get_coords

log = logging.getLogger(__name__)

BASE_URL = "https://aircorsica-rh.my.salesforce-sites.com/Recrutement"

PILOT_RE = re.compile(
    r'\b(pilots?|pilotes?|commandants?\s*de\s*bord|cdb|opl|copilotes?|'
    r'captains?|first officers?|f/o|flight crew|flight deck|a320|atr)\b',
    re.I
)
EXCLUDE_RE = re.compile(
    r'\b(cabin|h[ô]tesse|hotesse|steward|pnc|maintenance|technicien|escale|'
    r'commercial|vente|manager|comptable|informatique|rh|ressources humaines)\b',
    re.I
)


def scan() -> list[JobOffer] | None:
    found: list[JobOffer] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, wait_until='domcontentloaded', timeout=30000)

            # Wait for Lightning to inject job cards — selector may vary; try several
            try:
                page.wait_for_selector('.job-item', timeout=20000)
            except Exception:
                log.info("Air Corsica: aucun poste trouvé (portail vide ou timeout rendu)")
                browser.close()
                return found

            page.wait_for_timeout(2000)

            items = page.query_selector_all('.job-item')
            for item in items:
                title_el = item.query_selector('.slds-text-heading_medium')
                if not title_el:
                    continue

                title = title_el.inner_text().strip()
                if not title:
                    continue

                if not PILOT_RE.search(title):
                    continue
                if EXCLUDE_RE.search(title):
                    continue

                sf_id = item.get_attribute('data-id') or ''
                link = f"{BASE_URL}?jobOfferId={sf_id}" if sf_id else BASE_URL

                # City field has icon utility:checkin
                city_el = item.query_selector('[icon-name="utility:checkin"]')
                location = city_el.inner_text().strip() if city_el else 'Ajaccio'
                if not location:
                    location = 'Ajaccio'
                location = location.title()

                lat, lon = get_coords(location)
                found.append(JobOffer(
                    id=job_hash(title, link),
                    title=title,
                    link=link,
                    source='Air Corsica',
                    location=location,
                    lat=lat, lon=lon,
                ))

            browser.close()
        log.info(f"Air Corsica: {len(found)} offre(s) PNT")
    except Exception as e:
        log.error(f"Erreur Air Corsica: {e}")
        return None
    return found
