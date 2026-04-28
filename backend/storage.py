import os
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional
from models import JobOffer

DB_FILE = os.getenv("DB_FILE", "aerowatch.db")


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                link        TEXT NOT NULL,
                location    TEXT DEFAULT 'N/C',
                source      TEXT NOT NULL,
                status      TEXT DEFAULT 'active',
                lat         REAL DEFAULT 48.5,
                lon         REAL DEFAULT 10.0,
                first_seen  TEXT NOT NULL,
                last_seen   TEXT NOT NULL,
                notified    INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS geocache (
                location    TEXT PRIMARY KEY,
                lat         REAL NOT NULL,
                lon         REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meta (
                key         TEXT PRIMARY KEY,
                value       TEXT
            );
            CREATE TABLE IF NOT EXISTS source_status (
                source      TEXT PRIMARY KEY,
                last_check  TEXT NOT NULL,
                status      TEXT NOT NULL,   -- ok | error
                jobs_found  INTEGER DEFAULT 0,
                error_msg   TEXT,
                duration_ms INTEGER
            );
        """)


def job_hash(title: str, link: str) -> str:
    return hashlib.sha256(f"{title}||{link}".encode()).hexdigest()[:20]


def upsert_job(job: JobOffer) -> bool:
    """Insert or update a job. Returns True if the job is brand new."""
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_FILE) as conn:
        existing = conn.execute(
            "SELECT id FROM jobs WHERE id = ?", (job.id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE jobs SET last_seen = ?, status = ? WHERE id = ?",
                (now, job.status, job.id),
            )
            return False
        conn.execute(
            """INSERT INTO jobs
               (id, title, link, location, source, status, lat, lon, first_seen, last_seen, notified)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (job.id, job.title, job.link, job.location, job.source,
             job.status, job.lat, job.lon, now, now),
        )
        return True


def expire_missing_jobs(source: str, seen_ids: set[str]):
    """Mark active jobs from `source` that weren't seen in this scan as expired."""
    if not seen_ids:
        return
    placeholders = ",".join("?" * len(seen_ids))
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            f"""UPDATE jobs SET status = 'expired'
                WHERE source = ? AND status = 'active'
                AND id NOT IN ({placeholders})""",
            [source] + list(seen_ids),
        )


def mark_notified(job_id: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE jobs SET notified = 1 WHERE id = ?", (job_id,))


def get_jobs(source: Optional[str] = None,
             status: Optional[str] = None,
             q: Optional[str] = None) -> list[dict]:
    query = "SELECT * FROM jobs WHERE 1=1"
    params: list = []
    if source:
        query += " AND LOWER(source) = LOWER(?)"
        params.append(source)
    if status:
        query += " AND status = ?"
        params.append(status)
    if q:
        query += " AND (LOWER(title) LIKE ? OR LOWER(location) LIKE ?)"
        params += [f"%{q.lower()}%", f"%{q.lower()}%"]
    query += " ORDER BY first_seen DESC"
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_sources() -> list[str]:
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute(
            "SELECT DISTINCT source FROM jobs ORDER BY source"
        ).fetchall()
        return [r[0] for r in rows]


def get_stats() -> dict:
    with sqlite3.connect(DB_FILE) as conn:
        total   = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        active  = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='active'").fetchone()[0]
        full    = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='full'").fetchone()[0]
        expired = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='expired'").fetchone()[0]
        new_24h = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status='active' AND first_seen >= datetime('now','-48 hours')"
        ).fetchone()[0]
    return {"total": total, "active": active, "full": full, "expired": expired, "new_48h": new_24h}


def get_meta(key: str) -> Optional[str]:
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else None


def set_meta(key: str, value: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value)
        )


def update_source_status(source: str, status: str, jobs_found: int,
                         duration_ms: int, error_msg: Optional[str] = None):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO source_status
               (source, last_check, status, jobs_found, duration_ms, error_msg)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source, datetime.now().isoformat(), status, jobs_found, duration_ms, error_msg),
        )


def get_source_statuses() -> list[dict]:
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM source_status ORDER BY source"
        ).fetchall()
        return [dict(r) for r in rows]
