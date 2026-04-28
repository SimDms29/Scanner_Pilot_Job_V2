import os
import logging
import requests
from datetime import datetime
from models import JobOffer

log = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_new_jobs(new_jobs: list[JobOffer]):
    if not new_jobs:
        return
    if not DISCORD_WEBHOOK_URL:
        log.warning("DISCORD_WEBHOOK_URL manquant — notification ignorée.")
        return

    by_source: dict[str, list[JobOffer]] = {}
    for job in new_jobs:
        by_source.setdefault(job.source, []).append(job)

    embeds = []
    for source, jobs in by_source.items():
        fields = [
            {
                "name": f"✅ {j.title}",
                "value": f"📍 {j.location}\n[Voir l'offre]({j.link})",
                "inline": False,
            }
            for j in jobs
        ]
        embeds.append({
            "title": f"🏢 {source.upper()}",
            "color": 0x27E080,
            "fields": fields[:25],
        })

    payload = {
        "username": "AeroWatch",
        "content": (
            f"🆕 **{len(new_jobs)} nouvelle(s) offre(s) PNT détectée(s)** — "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ),
        "embeds": embeds[:10],
    }

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
        log.info(f"Discord notifié — {len(new_jobs)} nouvelles offres")
    except Exception as e:
        log.error(f"Erreur Discord: {e}")
