import sqlite3
import logging
from datetime import datetime, timezone

DB_PATH = "/app/logs/incidents.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                container TEXT NOT NULL,
                event     TEXT NOT NULL,
                attempt   INTEGER DEFAULT 0
            )
        """)
        conn.commit()


def record_event(container: str, event: str, attempt: int = 0):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO incidents (timestamp, container, event, attempt) VALUES (?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), container, event, attempt)
            )
            conn.commit()
    except Exception as e:
        logging.warning(f"[DB] Failed to record event: {e}")


def get_recent_incidents(limit: int = 50) -> list[dict]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM incidents ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logging.warning(f"[DB] Failed to fetch incidents: {e}")
        return []


def get_restart_counts() -> list[dict]:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT container, COUNT(*) as count
                FROM incidents WHERE event = 'restarted'
                GROUP BY container
            """).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logging.warning(f"[DB] Failed to fetch restart counts: {e}")
        return []
