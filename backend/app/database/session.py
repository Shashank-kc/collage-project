"""
CodeGuard AI - SQLite Database Manager
======================================
Stores past scan runs locally using Python's built-in sqlite3.
Provides aggregated analytics for the developer dashboard.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import logging
import sqlite3
from typing import Generator, List, Optional

from app.config import DATABASE_PATH
from app.schemas.analysis import DashboardMetrics, ScanHistoryItem

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
    """Initializes database schema and runs non-destructive migrations."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
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

        # Gracefully add 'status' column if migrating from an earlier table version
        try:
            cursor = conn.execute("PRAGMA table_info(scans)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "status" not in columns:
                conn.execute("ALTER TABLE scans ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'")
        except Exception as exc:
            logger.debug("Table migration note: %s", exc)

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
    source_code: str,
    status: str = "completed"
) -> int:
    """Saves a scan record and returns the new record ID."""
    # Preview up to 300 characters
    preview = source_code.strip()[:300]
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO scans (
                timestamp, filename, status, lines_analyzed, health_score, health_grade,
                total_findings, security_findings, quality_findings,
                execution_time_ms, code_preview
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_iso,
            filename,
            status,
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
            SELECT id, timestamp, status, total_findings, security_findings,
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
                status=row["status"] if "status" in row.keys() else "completed",
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


def get_scan_by_id(scan_id: int) -> Optional[ScanHistoryItem]:
    """Retrieves a single scan record by ID."""
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT id, timestamp, status, total_findings, security_findings,
                   quality_findings, health_score, health_grade,
                   execution_time_ms, code_preview
            FROM scans
            WHERE id = ?
        """, (scan_id,)).fetchone()

    if not row:
        return None

    return ScanHistoryItem(
        id=row["id"],
        timestamp=row["timestamp"],
        status=row["status"] if "status" in row.keys() else "completed",
        total_findings=row["total_findings"],
        security_findings=row["security_findings"],
        quality_findings=row["quality_findings"],
        health_score=row["health_score"],
        health_grade=row["health_grade"],
        execution_time_ms=row["execution_time_ms"],
        code_preview=row["code_preview"],
    )


def get_dashboard_metrics() -> DashboardMetrics:
    """Aggregates real scan history from SQLite for the developer dashboard."""
    with get_db_connection() as conn:
        # Total counts
        total_scans = conn.execute("SELECT COUNT(*) as count FROM scans").fetchone()["count"]
        completed_scans = conn.execute("SELECT COUNT(*) as count FROM scans WHERE status = 'completed'").fetchone()["count"]
        failed_scans = conn.execute("SELECT COUNT(*) as count FROM scans WHERE status != 'completed'").fetchone()["count"]

        # Average score & issue totals
        aggregates = conn.execute("""
            SELECT 
                AVG(health_score) as avg_score,
                SUM(security_findings) as sum_security,
                SUM(quality_findings) as sum_quality
            FROM scans
            WHERE status = 'completed'
        """).fetchone()

        avg_score = round(aggregates["avg_score"] or 100.0, 1) if aggregates else 100.0
        sum_security = aggregates["sum_security"] or 0 if aggregates else 0
        sum_quality = aggregates["sum_quality"] or 0 if aggregates else 0

        # Grade distribution
        grade_rows = conn.execute("""
            SELECT health_grade, COUNT(*) as count
            FROM scans
            WHERE status = 'completed'
            GROUP BY health_grade
        """).fetchall()

        grades = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for r in grade_rows:
            if r["health_grade"] in grades:
                grades[r["health_grade"]] = r["count"]

    recent = get_recent_scans(limit=5)

    return DashboardMetrics(
        total_scans=total_scans,
        completed_scans=completed_scans,
        failed_scans=failed_scans,
        average_health_score=avg_score,
        total_security_issues=sum_security,
        total_quality_issues=sum_quality,
        grade_distribution=grades,
        recent_scans=recent
    )
