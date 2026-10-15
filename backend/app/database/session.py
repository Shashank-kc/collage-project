"""
CodeGuard AI - SQLite Database Manager & User Data Isolation
============================================================
Stores past scan runs, user accounts, sessions, and AI conversations locally
using Python's built-in sqlite3.
Enforces multi-user isolation on scans, analytics, and assistant history.
"""

from contextlib import contextmanager
from datetime import datetime, timezone
import logging
import sqlite3
from typing import Generator, List, Optional, Dict, Any

from app.config import DATABASE_PATH
from app.schemas.analysis import DashboardMetrics, ScanHistoryItem

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database connection with foreign key support."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initializes database schema and runs safe, non-destructive migrations."""
    with get_db_connection() as conn:
        # 1. Scans Table
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
                code_preview TEXT NOT NULL,
                user_id INTEGER DEFAULT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp DESC)")

        # Run non-destructive column migrations on scans table
        try:
            cursor = conn.execute("PRAGMA table_info(scans)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "status" not in columns:
                conn.execute("ALTER TABLE scans ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'")
            if "user_id" not in columns:
                conn.execute("ALTER TABLE scans ADD COLUMN user_id INTEGER DEFAULT NULL")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id)")
        except Exception as exc:
            logger.debug("Scans table migration note: %s", exc)

        # 2. Users Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")

        # 3. Sessions Table (Stateful server sessions with TTL)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)")

        # 4. Conversations Table (AI Assistant Threads)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at DESC)")

        # 5. Messages Table (AI Assistant Messages within a Thread)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                finding_context TEXT DEFAULT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at ASC)")

    logger.info("SQLite database initialized and migrations applied at: %s", DATABASE_PATH)


# =========================================================================
# SCAN MANAGEMENT & USER ISOLATION
# =========================================================================

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
    status: str = "completed",
    user_id: Optional[int] = None
) -> int:
    """Saves a scan record associated with the authenticated user ID and returns new record ID."""
    preview = source_code.strip()[:300]
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO scans (
                timestamp, filename, status, lines_analyzed, health_score, health_grade,
                total_findings, security_findings, quality_findings,
                execution_time_ms, code_preview, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            preview,
            user_id
        ))
        return cursor.lastrowid or 0


def get_recent_scans(limit: int = 10, user_id: Optional[int] = None) -> List[ScanHistoryItem]:
    """
    Retrieves recent scan records ordered by most recent first.
    Enforces user isolation: authenticated users only see their own scans.
    """
    with get_db_connection() as conn:
        if user_id is not None:
            rows = conn.execute("""
                SELECT id, timestamp, status, total_findings, security_findings,
                       quality_findings, health_score, health_grade,
                       execution_time_ms, code_preview
                FROM scans
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()
        else:
            # Anonymous / unassigned legacy scans
            rows = conn.execute("""
                SELECT id, timestamp, status, total_findings, security_findings,
                       quality_findings, health_score, health_grade,
                       execution_time_ms, code_preview
                FROM scans
                WHERE user_id IS NULL
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


def get_scan_by_id(scan_id: int, user_id: Optional[int] = None) -> Optional[ScanHistoryItem]:
    """Retrieves a single scan record by ID with authorization verification."""
    with get_db_connection() as conn:
        if user_id is not None:
            row = conn.execute("""
                SELECT id, timestamp, status, total_findings, security_findings,
                       quality_findings, health_score, health_grade,
                       execution_time_ms, code_preview
                FROM scans
                WHERE id = ? AND (user_id = ? OR user_id IS NULL)
            """, (scan_id, user_id)).fetchone()
        else:
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


def get_dashboard_metrics(user_id: Optional[int] = None) -> DashboardMetrics:
    """Aggregates scan history from SQLite for the developer dashboard, isolated per user."""
    with get_db_connection() as conn:
        if user_id is not None:
            user_filter = "user_id = ?"
            params = (user_id,)
            completed_filter = "status = 'completed' AND user_id = ?"
            failed_filter = "status != 'completed' AND user_id = ?"
        else:
            user_filter = "user_id IS NULL"
            params = ()
            completed_filter = "status = 'completed' AND user_id IS NULL"
            failed_filter = "status != 'completed' AND user_id IS NULL"

        total_scans = conn.execute(
            f"SELECT COUNT(*) as count FROM scans WHERE {user_filter}", params
        ).fetchone()["count"]

        completed_scans = conn.execute(
            f"SELECT COUNT(*) as count FROM scans WHERE {completed_filter}", params
        ).fetchone()["count"]

        failed_scans = conn.execute(
            f"SELECT COUNT(*) as count FROM scans WHERE {failed_filter}", params
        ).fetchone()["count"]

        aggregates = conn.execute(f"""
            SELECT 
                AVG(health_score) as avg_score,
                SUM(security_findings) as sum_security,
                SUM(quality_findings) as sum_quality
            FROM scans
            WHERE {completed_filter}
        """, params).fetchone()

        avg_score = round(aggregates["avg_score"] or 100.0, 1) if aggregates and aggregates["avg_score"] is not None else 100.0
        sum_security = aggregates["sum_security"] or 0 if aggregates and aggregates["sum_security"] is not None else 0
        sum_quality = aggregates["sum_quality"] or 0 if aggregates and aggregates["sum_quality"] is not None else 0

        grade_rows = conn.execute(f"""
            SELECT health_grade, COUNT(*) as count
            FROM scans
            WHERE {completed_filter}
            GROUP BY health_grade
        """, params).fetchall()

        grades = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for r in grade_rows:
            if r["health_grade"] in grades:
                grades[r["health_grade"]] = r["count"]

    recent = get_recent_scans(limit=5, user_id=user_id)

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


# =========================================================================
# USER & SESSION REPOSITORY (ARGON2ID + SECURE COOKIES)
# =========================================================================

def create_user(email: str, password_hash: str, full_name: str) -> Dict[str, Any]:
    """Persists a new user record with securely hashed password."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO users (email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?)
        """, (email.lower().strip(), password_hash, full_name.strip(), now_iso))
        user_id = cursor.lastrowid
        return {
            "id": user_id,
            "email": email.lower().strip(),
            "full_name": full_name.strip(),
            "created_at": now_iso
        }


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves user by normalized email address."""
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT id, email, password_hash, full_name, created_at
            FROM users
            WHERE email = ?
        """, (email.lower().strip(),)).fetchone()

    if not row:
        return None
    return dict(row)


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves safe user profile by ID without password hash."""
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT id, email, full_name, created_at
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

    if not row:
        return None
    return dict(row)


def create_session(session_id: str, user_id: int, expires_at: str) -> None:
    """Stores an authenticated session token with expiration."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO sessions (session_id, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, user_id, now_iso, expires_at))


def get_session_user(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Validates a session token, checks TTL expiration, and returns the user object.
    Automatically deletes expired sessions.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT u.id, u.email, u.full_name, u.created_at, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_id = ?
        """, (session_id,)).fetchone()

        if not row:
            return None

        # Check expiration
        if row["expires_at"] <= now_iso:
            # Session expired: clean up
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            return None

        return {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "created_at": row["created_at"]
        }


def delete_session(session_id: str) -> None:
    """Invalidates an active session token on logout."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def delete_user_sessions(user_id: int) -> None:
    """Invalidates all sessions for a specific user."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


# =========================================================================
# AI ASSISTANT CHAT CONVERSATIONS REPOSITORY
# =========================================================================

def create_conversation(conv_id: str, user_id: int, title: str) -> Dict[str, Any]:
    """Creates a new AI Assistant conversation associated with the authenticated user."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO conversations (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (conv_id, user_id, title.strip()[:100], now_iso, now_iso))
    return {
        "id": conv_id,
        "user_id": user_id,
        "title": title.strip()[:100],
        "created_at": now_iso,
        "updated_at": now_iso
    }


def get_user_conversations(user_id: int) -> List[Dict[str, Any]]:
    """Retrieves all conversation metadata belonging exclusively to the user."""
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,)).fetchall()
    return [dict(r) for r in rows]


def get_conversation(conv_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single conversation ensuring user ownership."""
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT id, user_id, title, created_at, updated_at
            FROM conversations
            WHERE id = ? AND user_id = ?
        """, (conv_id, user_id)).fetchone()
    if not row:
        return None
    return dict(row)


def delete_conversation(conv_id: str, user_id: int) -> bool:
    """Deletes a conversation and its messages, enforcing user authorization."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            DELETE FROM conversations
            WHERE id = ? AND user_id = ?
        """, (conv_id, user_id))
        return cursor.rowcount > 0


def save_message(
    msg_id: str,
    conv_id: str,
    sender: str,
    content: str,
    finding_context: Optional[str] = None
) -> Dict[str, Any]:
    """Stores a chat message within an authorized conversation thread."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO messages (id, conversation_id, sender, content, finding_context, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (msg_id, conv_id, sender, content, finding_context, now_iso))

        # Update conversation updated_at
        conn.execute("""
            UPDATE conversations
            SET updated_at = ?
            WHERE id = ?
        """, (now_iso, conv_id))

    return {
        "id": msg_id,
        "conversation_id": conv_id,
        "sender": sender,
        "content": content,
        "finding_context": finding_context,
        "created_at": now_iso
    }


def get_conversation_messages(conv_id: str, user_id: int) -> Optional[List[Dict[str, Any]]]:
    """Retrieves all messages for a conversation, validating user ownership."""
    with get_db_connection() as conn:
        # Check ownership first
        owner = conn.execute("""
            SELECT id FROM conversations WHERE id = ? AND user_id = ?
        """, (conv_id, user_id)).fetchone()

        if not owner:
            return None

        rows = conn.execute("""
            SELECT id, conversation_id, sender, content, finding_context, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conv_id,)).fetchall()

    return [dict(r) for r in rows]
