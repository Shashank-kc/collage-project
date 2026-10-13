"""
CodeGuard AI - API Endpoints
=============================
Defines the REST API routes for code analysis, scan history, health checks,
and educational code samples.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.config import MAX_CODE_SIZE_BYTES, RUFF_PATH, BANDIT_PATH
from app.database.session import get_recent_scans, save_scan_record
from app.schemas.analysis import (
    CodeAnalysisRequest,
    CodeAnalysisResponse,
    ScanHistoryItem,
)
from app.services.coordinator import AnalysisCoordinator

router = APIRouter(prefix="/api/v1", tags=["Analysis"])
coordinator = AnalysisCoordinator()

# Curated sample scripts for instant testing
SAMPLE_CODES = {
    "vulnerable": (
        'import os\n'
        'import sys\n'
        'import hashlib\n'
        '\n'
        '# Insecure database query simulation\n'
        'def get_user_profile(user_input_id):\n'
        '    # WARNING: SQL Injection vulnerability via string formatting\n'
        '    query = f"SELECT * FROM users WHERE id = {user_input_id}"\n'
        '    print("Executing:", query)\n'
        '\n'
        '# Hardcoded credentials\n'
        'DATABASE_PASSWORD = "super_secret_admin_password_123"\n'
        '\n'
        'def verify_token(token):\n'
        '    # Insecure use of assert in control flow\n'
        '    assert token is not None, "Token must exist"\n'
        '    \n'
        '    # Insecure hash algorithm (MD5)\n'
        '    token_hash = hashlib.md5(token.encode()).hexdigest()\n'
        '    return token_hash\n'
        '\n'
        'def run_calculation(expression):\n'
        '    # Dangerous dynamic code execution\n'
        '    return eval(expression)\n'
        '\n'
        'def process_items(items=[]):\n'
        '    # Mutable default argument bug\n'
        '    items.append(1)\n'
        '    return items\n'
    ),
    "clean": (
        '"""\n'
        'Clean, robust Python module demonstrating secure coding practices.\n'
        '"""\n'
        'from typing import List, Optional\n'
        'import hashlib\n'
        'import os\n'
        '\n'
        '\n'
        'def get_user_profile(user_id: int) -> dict:\n'
        '    """Uses parameterized queries to prevent SQL injection."""\n'
        '    # In a real app: cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n'
        '    return {"user_id": user_id, "status": "active"}\n'
        '\n'
        '\n'
        'def verify_token(token: str) -> str:\n'
        '    """Validates token using secure hashing (SHA-256)."""\n'
        '    if not token:\n'
        '        raise ValueError("Token must not be empty")\n'
        '    return hashlib.sha256(token.encode()).hexdigest()\n'
        '\n'
        '\n'
        'def get_database_password() -> Optional[str]:\n'
        '    """Reads credentials securely from environment variables."""\n'
        '    return os.getenv("DATABASE_PASSWORD")\n'
        '\n'
        '\n'
        'def append_item(item: int, items: Optional[List[int]] = None) -> List[int]:\n'
        '    """Avoids mutable default argument anti-pattern."""\n'
        '    if items is None:\n'
        '        items = []\n'
        '    items.append(item)\n'
        '    return items\n'
    )
}


@router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(payload: CodeAnalysisRequest) -> CodeAnalysisResponse:
    """
    Submits Python source code for static analysis with Ruff and Bandit.
    Code is inspected strictly using static AST parsers and NEVER executed.
    """
    raw_code = payload.code

    # Input validation: check for empty or whitespace-only code
    if not raw_code or not raw_code.strip():
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Source code cannot be empty."
        )

    # Input validation: payload size limitation
    code_bytes = len(raw_code.encode("utf-8"))
    if code_bytes > MAX_CODE_SIZE_BYTES:
        raise HTTPException(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            detail=f"Code size ({code_bytes} bytes) exceeds maximum limit of {MAX_CODE_SIZE_BYTES} bytes (100 KB)."
        )

    # Execute static analysis pipeline
    response = coordinator.run_analysis(raw_code, payload.filename or "submission.py")

    # Persist summary to SQLite database
    try:
        scan_id = save_scan_record(
            filename=payload.filename or "submission.py",
            lines_analyzed=response.lines_analyzed,
            health_score=response.summary.health_score,
            health_grade=response.summary.health_grade,
            total_findings=response.summary.total_findings,
            security_findings=response.summary.security_findings,
            quality_findings=response.summary.quality_findings,
            execution_time_ms=response.execution_time_ms,
            source_code=raw_code
        )
        response.scan_id = scan_id
    except Exception as exc:
        # DB failure should not prevent analysis results from returning
        print(f"Warning: Failed to save scan to database: {exc}")

    return response


@router.get("/history", response_model=List[ScanHistoryItem])
async def list_recent_scans(limit: int = 10) -> List[ScanHistoryItem]:
    """Retrieves recent scan records from SQLite history."""
    clamped_limit = max(1, min(limit, 50))
    return get_recent_scans(clamped_limit)


@router.get("/samples")
async def get_sample_codes():
    """Returns preset vulnerable and clean sample code for one-click testing."""
    return SAMPLE_CODES


@router.get("/health")
async def health_check():
    """Health check endpoint confirming service status and tool availability."""
    from pathlib import Path
    return {
        "status": "healthy",
        "service": "CodeGuard AI Backend",
        "tools": {
            "ruff": {"configured_path": RUFF_PATH, "available": Path(RUFF_PATH).exists()},
            "bandit": {"configured_path": BANDIT_PATH, "available": Path(BANDIT_PATH).exists()},
        }
    }
