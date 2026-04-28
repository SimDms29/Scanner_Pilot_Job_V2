import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

import storage
import scanner

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    sched = BackgroundScheduler()
    sched.add_job(
        lambda: scanner.run_scan(notify_discord=True),
        "interval",
        hours=scanner.CHECK_INTERVAL_HOURS,
        id="auto_scan",
    )
    sched.start()
    t = threading.Thread(target=scanner.run_scan, kwargs={"notify_discord": False}, daemon=True)
    t.start()
    yield
    sched.shutdown(wait=False)


app = FastAPI(title="AeroWatch", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/jobs")
def get_jobs(source: str = None, status: str = None, q: str = None):
    jobs = storage.get_jobs(source=source, status=status, q=q)
    stats = storage.get_stats()
    return {
        "jobs": jobs,
        "total": len(jobs),
        "last_scan": storage.get_meta("last_scan"),
        "next_scan": storage.get_meta("next_scan"),
        "scan_running": scanner.is_running(),
        **stats,
    }


@app.get("/api/sources")
def get_sources():
    return {"sources": storage.get_sources()}


@app.get("/api/status")
def get_status():
    stats = storage.get_stats()
    return {
        **stats,
        "last_scan": storage.get_meta("last_scan"),
        "next_scan": storage.get_meta("next_scan"),
        "scan_running": scanner.is_running(),
    }


@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks):
    if scanner.is_running():
        return {"message": "Scan déjà en cours", "status": "running"}
    background_tasks.add_task(scanner.run_scan, False)
    return {"message": "Scan lancé", "status": "started"}


@app.get("/api/scanner")
def get_scanner_status():
    return {
        "sources": storage.get_source_statuses(),
        "last_scan": storage.get_meta("last_scan"),
        "next_scan": storage.get_meta("next_scan"),
        "scan_running": scanner.is_running(),
    }


@app.get("/", response_class=HTMLResponse)
def index():
    with open("index.html") as f:
        return f.read()
