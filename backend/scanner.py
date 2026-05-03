import logging
import threading
import time
from datetime import datetime, timedelta

from storage import upsert_job, expire_missing_jobs, mark_notified, set_meta, update_source_status
from notifications import send_new_jobs
from scrapers.ats import bamboohr, recruitee
from scrapers.companies import amelia, netjets, la_compagnie, chalair, pan_europeenne, helvetic, elitavia, avconjet, flyinggroup, air_alliance, dat, loganair, jetaviation, vistajet, luxair, platoon, gamaaviation, wideroe
from models import JobOffer

log = logging.getLogger(__name__)

CHECK_INTERVAL_HOURS = 12

_scan_running = False
_lock = threading.Lock()

BAMBOOHR_COMPANIES = [
    ("jetfly",      "Jetfly",       "Luxembourg"),
    ("comlux",      "Comlux",       "Luxembourg"),
    ("luxaviation", "Luxaviation",  "Luxembourg"),
]

RECRUITEE_COMPANIES = [
    ("dcaviationgmbh", "DC Aviation",  "Stuttgart"),
    ("tagaviation3",   "TAG Aviation", "Geneva"),
]

CUSTOM_SCRAPERS = [
    ("Amelia",           amelia.scan),
    ("NetJets Europe",   netjets.scan),
    ("La Compagnie",     la_compagnie.scan),
    ("Chalair",          chalair.scan),
    ("Pan Européenne",   pan_europeenne.scan),
    ("Helvetic Airways", helvetic.scan),
    ("Elit'Avia",        elitavia.scan),
    ("Avcon Jet",        avconjet.scan),
    ("Flying Group",          flyinggroup.scan),
    ("Air Alliance",          air_alliance.scan),
    ("Danish Air Transport",  dat.scan),
    ("Loganair",              loganair.scan),
    ("Jet Aviation",          jetaviation.scan),
    ("VistaJet",              vistajet.scan),
    ("Luxair",                luxair.scan),
    ("Platoon Aviation",      platoon.scan),
    ("Gama Aviation",         gamaaviation.scan),
    ("Widerøe",               wideroe.scan),
]


def is_running() -> bool:
    return _scan_running


def _run_source(name: str, results: list[JobOffer] | None, duration_ms: int) -> list[JobOffer]:
    """Upsert jobs, expire missing ones, record status, return list of new jobs."""
    if results is None:
        update_source_status(name, "error", 0, duration_ms, "Erreur réseau ou timeout")
        log.warning(f"{name}: scan en erreur, expiry ignorée")
        return []
    new: list[JobOffer] = []
    seen_ids: set[str] = set()
    for job in results:
        if upsert_job(job):
            new.append(job)
        seen_ids.add(job.id)
    expire_missing_jobs(name, seen_ids)
    update_source_status(name, "ok", len(results), duration_ms)
    return new


def _timed_scan(name: str, fn, *args) -> tuple[list[JobOffer] | None, int]:
    """Run a scraper function, return (results, duration_ms)."""
    t0 = time.monotonic()
    results = fn(*args)
    return results, int((time.monotonic() - t0) * 1000)


def run_scan(notify_discord: bool = False):
    global _scan_running
    with _lock:
        if _scan_running:
            log.warning("Scan déjà en cours, skip.")
            return
        _scan_running = True

    log.info(f"=== SCAN LANCÉ {datetime.now().strftime('%d/%m/%Y %H:%M')} ===")
    new_jobs: list[JobOffer] = []

    try:
        for slug, name, default_loc in BAMBOOHR_COMPANIES:
            results, ms = _timed_scan(name, bamboohr.scan, slug, name, default_loc)
            new_jobs += _run_source(name, results, ms)

        for slug, name, default_loc in RECRUITEE_COMPANIES:
            results, ms = _timed_scan(name, recruitee.scan, slug, name, default_loc)
            new_jobs += _run_source(name, results, ms)

        for name, fn in CUSTOM_SCRAPERS:
            results, ms = _timed_scan(name, fn)
            new_jobs += _run_source(name, results, ms)

        now = datetime.now()
        set_meta("last_scan", now.isoformat())
        set_meta("next_scan", (now + timedelta(hours=CHECK_INTERVAL_HOURS)).isoformat())

        log.info(f"=== SCAN TERMINÉ — {len(new_jobs)} nouvelle(s) offre(s) ===")

        if notify_discord and new_jobs:
            send_new_jobs(new_jobs)
            for job in new_jobs:
                mark_notified(job.id)
        elif notify_discord:
            log.info("Aucune nouvelle offre — Discord non notifié")

    finally:
        with _lock:
            _scan_running = False
