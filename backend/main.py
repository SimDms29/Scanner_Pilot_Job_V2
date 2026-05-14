import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
        scanner.run_scan,
        "interval",
        hours=scanner.CHECK_INTERVAL_HOURS,
        id="auto_scan",
    )
    sched.start()
    t = threading.Thread(target=scanner.run_scan, daemon=True)
    t.start()
    yield
    sched.shutdown(wait=False)


SCAN_API_KEY = os.getenv("SCAN_API_KEY", "")

app = FastAPI(title="WingJobs", lifespan=lifespan, docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jobs.wingfuel.fr"],
    allow_methods=["GET", "POST"],
    allow_headers=["X-Scan-Key"],
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
def trigger_scan(background_tasks: BackgroundTasks, x_scan_key: str = Header(default="")):
    if not SCAN_API_KEY or x_scan_key != SCAN_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
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


DIST = Path(__file__).parent.parent / "frontend" / "dist"

if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str = ""):
        if full_path.startswith("api"):
            return {"error": "not found"}
        return FileResponse(DIST / "index.html")
