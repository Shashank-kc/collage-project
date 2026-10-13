"""
CodeGuard AI - SQLite Database Manager
======================================
Stores past scan runs locally using Python's built-in sqlite3.
No heavy database server required—ideal for development and learning.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
from typing import Generator, List

from app.config import DATABASE_PATH
from app.schemas.analysis import ScanHistoryItem

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initializes database tables if they do not exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                lines_analyzed INTEGER NOT NULL,
                health_score INTEGER NOT NULL,
                health_grade TEXT NOT NULL,
                total_findings INTEGER NOT NULL,
                security_findings INTEGER NOT NULL,
                quality_findings INTEGER NOT NULL,
                execution_time_ms REAL NOT NULL,
                code_preview TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp DESC)")
    logger.info("SQLite database initialized at: %s", DATABASE_PATH)


def save_scan_record(
    filename: str,
    lines_analyzed: int,
    health_score: int,
    health_grade: str,
    total_findings: int,
    security_findings: int,
    quality_findings: int,
    execution_time_ms: float,
    source_code: str
) -> int:
    """Saves a scan record and returns the new record ID."""
    # Preview up to 300 characters
    preview = source_code.strip()[:300]
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO scans (
                timestamp, filename, lines_analyzed, health_score, health_grade,
                total_findings, security_findings, quality_findings,
                execution_time_ms, code_preview
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_iso,
            filename,
            lines_analyzed,
            health_score,
            health_grade,
            total_findings,
            security_findings,
            quality_findings,
            execution_time_ms,
            preview
        ))
        return cursor.lastrowid or 0


def get_recent_scans(limit: int = 10) -> List[ScanHistoryItem]:
    """Retrieves recent scan records ordered by most recent first."""
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT id, timestamp, total_findings, security_findings,
                   quality_findings, health_score, health_grade,
                   execution_time_ms, code_preview
            FROM scans
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    items = []
    for row in rows:
        items.append(
            ScanHistoryItem(
                id=row["id"],
                timestamp=row["timestamp"],
                total_findings=row["total_findings"],
                security_findings=row["security_findings"],
                quality_findings=row["quality_findings"],
                health_score=row["health_score"],
                health_grade=row["health_grade"],
                execution_time_ms=row["execution_time_ms"],
                code_preview=row["code_preview"],
            )
        )
    return items
